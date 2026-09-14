from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any, Protocol

import pandas as pd

from .crm import build_hubspot_payloads
from .dedupe import deduplicate_dataframe, prospect_identity_key
from .models import ProspectRecord
from .normalize import normalize_dataframe
from .routing import route_score
from .scoring import score_prospect


class CRMAdapter(Protocol):
    def upsert(self, bundle: Any) -> dict[str, Any]: ...


def _clean_missing(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_missing(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_missing(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def make_idempotency_key(record: ProspectRecord, schema_version: str = "v1") -> str:
    payload = record.model_dump(mode="json")
    identity = prospect_identity_key(payload)
    source_record_id = record.source_record_id or ""
    raw = f"{schema_version}|{identity}|{source_record_id}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"gtm:{digest}"


def process_dataframe(
    df: pd.DataFrame,
    config: Mapping[str, Any],
    crm_adapter: CRMAdapter,
) -> list[dict[str, Any]]:
    normalized = normalize_dataframe(df)
    deduped = deduplicate_dataframe(normalized)
    results: list[dict[str, Any]] = []

    for row in deduped.to_dict(orient="records"):
        cleaned = _clean_missing(row)
        record = ProspectRecord.model_validate(cleaned)
        score = score_prospect(record, config)
        routing = route_score(score.total, config)
        bundle = build_hubspot_payloads(record, score, routing)
        crm_result = crm_adapter.upsert(bundle)
        results.append(
            {
                "status": "processed",
                "idempotency_key": make_idempotency_key(record),
                "prospect": record.model_dump(mode="json"),
                "score": score.model_dump(mode="json"),
                "routing": routing.model_dump(mode="json"),
                "crm_payload": bundle.model_dump(mode="json"),
                "crm": crm_result,
            }
        )
    return results
