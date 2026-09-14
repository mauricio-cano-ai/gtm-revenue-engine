from fastapi.testclient import TestClient

from gtm_engine.api import create_app


SAMPLE = {
    "schema_version": "v1",
    "company_name": "Northstar Labs",
    "domain": "https://www.northstar.example/path",
    "person_name": "Avery Stone",
    "title": "VP Growth",
    "email": "avery@northstar.example",
    "source": "clay",
    "source_record_id": "clay-001",
    "firmographic_fit": 1.0,
    "technographic_fit": 1.0,
    "hiring_signal": 1.0,
    "funding_signal": 1.0,
    "intent_signal": 1.0,
    "behavioral_signal": 0.5,
}


def test_health_reports_service_ready():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gtm-revenue-engine"}


def test_score_endpoint_preserves_record_and_adds_score_and_routing():
    client = TestClient(create_app())

    response = client.post("/score", json=SAMPLE, headers={"X-Idempotency-Key": "gtm:test:1"})

    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "northstar.example"
    assert body["score"]["total"] == 95
    assert body["routing"] == {
        "tier": "A",
        "action": "immediate_sales_routing",
        "owner": "senior_ae_queue",
    }
    assert body["idempotency_key"] == "gtm:test:1"


def test_crm_upsert_endpoint_accepts_score_response_and_returns_mock_result():
    client = TestClient(create_app())
    scored = client.post("/score", json=SAMPLE, headers={"X-Idempotency-Key": "gtm:test:2"}).json()

    first = client.post("/crm/upsert", json=scored, headers={"X-Idempotency-Key": "gtm:test:2"})
    second = client.post("/crm/upsert", json=scored, headers={"X-Idempotency-Key": "gtm:test:2"})

    assert first.status_code == 200
    assert second.status_code == 200
    body = first.json()
    assert body["crm"]["status"] == "mock_upserted"
    assert body["crm"]["company_id"] == second.json()["crm"]["company_id"]
    assert body["crm_payload"]["company"]["properties"]["gtm_tier"] == "A"
    assert body["idempotency_key"] == "gtm:test:2"


def test_score_rejects_payload_without_company_identity():
    client = TestClient(create_app())

    response = client.post("/score", json={"source_record_id": "bad-1"})

    assert response.status_code == 422
