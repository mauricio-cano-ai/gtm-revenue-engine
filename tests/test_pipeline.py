import pandas as pd

from gtm_engine.crm import MockCRMAdapter
from gtm_engine.pipeline import process_dataframe
from gtm_engine.scoring import load_scoring_config


def test_pipeline_deduplicates_scores_routes_and_upserts():
    df = pd.DataFrame([
        {
            "company_name": "Acme",
            "domain": "https://www.acme.com",
            "person_name": "Ada Lovelace",
            "email": "ada@acme.com",
            "source": "clay",
            "source_record_id": "clay-001",
            "firmographic_fit": 1.0,
            "technographic_fit": 1.0,
            "hiring_signal": 0.8,
            "funding_signal": 0.8,
            "intent_signal": 1.0,
            "behavioral_signal": 0.9,
        },
        {
            "company_name": "Acme",
            "domain": "acme.com",
            "email": None,
            "source": "clay",
            "firmographic_fit": 0.4,
        },
        {
            "company_name": "Beta Labs",
            "domain": "beta.example",
            "source": "webinar",
            "firmographic_fit": 0.6,
            "technographic_fit": 0.5,
            "intent_signal": 0.2,
        },
    ])
    config = load_scoring_config("config/scoring.yaml")
    results = process_dataframe(df, config, MockCRMAdapter())

    assert len(results) == 2
    acme = next(item for item in results if item["prospect"]["domain"] == "acme.com")
    assert acme["score"]["total"] >= 80
    assert acme["routing"]["tier"] == "A"
    assert acme["crm"]["status"] == "mock_upserted"
    assert acme["idempotency_key"].startswith("gtm:")
    assert acme["status"] == "processed"


def test_pipeline_idempotency_key_is_stable_for_same_record():
    df = pd.DataFrame([{"company_name": "Acme", "domain": "acme.com", "source_record_id": "x1"}])
    config = load_scoring_config("config/scoring.yaml")
    first = process_dataframe(df, config, MockCRMAdapter())[0]
    second = process_dataframe(df, config, MockCRMAdapter())[0]
    assert first["idempotency_key"] == second["idempotency_key"]
