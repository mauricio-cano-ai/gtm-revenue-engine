import json
from pathlib import Path


WORKFLOW = Path("n8n/gtm-revenue-engine.workflow.json")


def test_n8n_workflow_contains_required_operational_nodes():
    data = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    names = {node["name"] for node in data["nodes"]}
    required = {
        "Clay Webhook",
        "Validate & Normalize",
        "Valid Payload?",
        "Quarantine Invalid",
        "Score via GTM Engine",
        "Tier Routing",
        "CRM Upsert",
        "Audit Success",
        "Respond Success",
        "Respond Quarantine",
    }
    assert required <= names


def test_workflow_is_sanitized_and_retry_aware():
    data = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    raw = WORKFLOW.read_text(encoding="utf-8").lower()
    assert "credentials" not in raw
    assert "pat-" not in raw
    assert "bearer ey" not in raw
    http_nodes = [node for node in data["nodes"] if node["type"] == "n8n-nodes-base.httpRequest"]
    assert http_nodes
    assert all(node.get("retryOnFail") is True for node in http_nodes)
    assert all(node.get("maxTries", 0) >= 3 for node in http_nodes)


def test_workflow_uses_environment_driven_endpoints():
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "$env.GTM_ENGINE_SCORE_URL" in raw
    assert "$env.GTM_CRM_UPSERT_URL" in raw


def test_env_example_wires_n8n_to_local_api_endpoints():
    env_text = Path(".env.example").read_text(encoding="utf-8")
    assert "GTM_ENGINE_SCORE_URL=http://localhost:8000/score" in env_text
    assert "GTM_CRM_UPSERT_URL=http://localhost:8000/crm/upsert" in env_text
    assert "GTM_CRM_MODE=mock" in env_text
