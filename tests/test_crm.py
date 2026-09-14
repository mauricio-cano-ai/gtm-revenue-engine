from datetime import datetime, timezone

import pytest

from gtm_engine.crm import (
    HubSpotCRMAdapter,
    MockCRMAdapter,
    build_hubspot_payloads,
    should_retry_status,
)
from gtm_engine.models import ProspectRecord, RoutingDecision, ScoreBreakdown


def _bundle():
    record = ProspectRecord(
        company_name="Acme Inc",
        domain="acme.com",
        person_name="Ada Lovelace",
        title="VP Growth",
        email="ada@acme.com",
        industry="SaaS",
        employee_count=250,
        source="clay",
    )
    score = ScoreBreakdown(total=88, components={"intent_signal": 20})
    route = RoutingDecision(tier="A", action="immediate_sales_routing", owner="senior_ae_queue")
    return build_hubspot_payloads(
        record,
        score,
        route,
        synced_at=datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc),
    )


def test_hubspot_payload_preserves_score_source_and_route():
    bundle = _bundle()
    company = bundle.company["properties"]
    contact = bundle.contact["properties"]
    assert company["domain"] == "acme.com"
    assert company["gtm_score"] == "88"
    assert company["gtm_tier"] == "A"
    assert company["gtm_source"] == "clay"
    assert company["gtm_route_action"] == "immediate_sales_routing"
    assert contact["email"] == "ada@acme.com"
    assert contact["firstname"] == "Ada"
    assert contact["lastname"] == "Lovelace"


def test_mock_adapter_returns_deterministic_ids():
    bundle = _bundle()
    adapter = MockCRMAdapter()
    first = adapter.upsert(bundle)
    second = adapter.upsert(bundle)
    assert first == second
    assert first["status"] == "mock_upserted"


def test_retry_classifier_only_retries_429_and_5xx():
    assert should_retry_status(429)
    assert should_retry_status(500)
    assert should_retry_status(503)
    assert not should_retry_status(400)
    assert not should_retry_status(401)
    assert not should_retry_status(404)


def test_real_adapter_requires_token():
    with pytest.raises(ValueError, match="HUBSPOT_ACCESS_TOKEN"):
        HubSpotCRMAdapter(access_token="")
