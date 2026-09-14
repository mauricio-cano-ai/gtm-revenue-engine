from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any

import uvicorn
from fastapi import FastAPI, Header

from .crm import HubSpotCRMAdapter, MockCRMAdapter, build_hubspot_payloads
from .models import ProspectRecord, RoutingDecision, ScoreBreakdown
from .routing import route_score
from .scoring import load_scoring_config, score_prospect


def _default_config_path() -> Path:
    return Path(os.getenv("GTM_SCORING_CONFIG", "config/scoring.yaml"))


def _default_crm_adapter() -> MockCRMAdapter | HubSpotCRMAdapter:
    mode = os.getenv("GTM_CRM_MODE", "mock").strip().lower()
    if mode == "hubspot":
        return HubSpotCRMAdapter()
    if mode != "mock":
        raise ValueError("GTM_CRM_MODE must be 'mock' or 'hubspot'")
    return MockCRMAdapter()


def create_app(
    *,
    config_path: str | Path | None = None,
    crm_adapter: MockCRMAdapter | HubSpotCRMAdapter | None = None,
) -> FastAPI:
    config = load_scoring_config(config_path or _default_config_path())
    adapter = crm_adapter or _default_crm_adapter()
    app = FastAPI(title="GTM Revenue Engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "gtm-revenue-engine"}

    @app.post("/score")
    def score(
        record: ProspectRecord,
        x_idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        score_result = score_prospect(record, config)
        routing = route_score(score_result.total, config)
        payload = record.model_dump(mode="json")
        payload["score"] = score_result.model_dump(mode="json")
        payload["routing"] = routing.model_dump(mode="json")
        if x_idempotency_key:
            payload["idempotency_key"] = x_idempotency_key
        return payload

    @app.post("/crm/upsert")
    def crm_upsert(
        body: dict[str, Any],
        x_idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        record = ProspectRecord.model_validate(body)
        score_result = ScoreBreakdown.model_validate(body["score"])
        routing = RoutingDecision.model_validate(body["routing"])
        bundle = build_hubspot_payloads(record, score_result, routing)
        crm_result = adapter.upsert(bundle)
        response = dict(body)
        response["crm_payload"] = bundle.model_dump(mode="json")
        response["crm"] = crm_result
        if x_idempotency_key:
            response["idempotency_key"] = x_idempotency_key
        return response

    return app


app = create_app()


def main() -> None:
    host = os.getenv("GTM_API_HOST", "0.0.0.0")
    port = int(os.getenv("GTM_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
