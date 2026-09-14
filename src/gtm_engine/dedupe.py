from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

import pandas as pd

from .normalize import normalize_domain


def _clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return " ".join(str(value).strip().lower().split())


def prospect_identity_key(record: Mapping[str, Any]) -> str:
    domain = normalize_domain(record.get("domain"))
    if domain:
        return f"domain:{domain}"
    company = _clean_text(record.get("company_name"))
    location = _clean_text(record.get("location"))
    if company:
        raw = f"{company}|{location}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"company:{digest}"
    email = _clean_text(record.get("email"))
    if email:
        return f"email:{email}"
    raw = repr(sorted((str(k), str(v)) for k, v in record.items()))
    return f"record:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _completeness(record: Mapping[str, Any]) -> int:
    score = 0
    for value in record.values():
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple, dict, set)) and not value:
            continue
        score += 1
    return score


def deduplicate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    candidates: dict[str, tuple[int, int, dict[str, Any]]] = {}
    for index, row in df.iterrows():
        record = row.to_dict()
        key = prospect_identity_key(record)
        completeness = _completeness(record)
        current = candidates.get(key)
        if current is None or completeness > current[0]:
            candidates[key] = (completeness, int(index) if isinstance(index, int) else 0, record)
    rows = [entry[2] for entry in candidates.values()]
    return pd.DataFrame(rows).reset_index(drop=True)
