import pandas as pd

from gtm_engine.dedupe import deduplicate_dataframe, prospect_identity_key


def test_identity_key_uses_normalized_domain_when_available():
    assert prospect_identity_key({"domain": "https://www.Acme.com/x"}) == "domain:acme.com"


def test_dedupe_prefers_record_with_more_enrichment():
    df = pd.DataFrame([
        {"company_name": "Acme", "domain": "acme.com", "email": None, "employee_count": 100},
        {"company_name": "Acme", "domain": "https://www.acme.com", "email": "buyer@acme.com", "employee_count": 100},
    ])
    out = deduplicate_dataframe(df)
    assert len(out) == 1
    assert out.iloc[0]["email"] == "buyer@acme.com"


def test_dedupe_preserves_distinct_companies_without_domains():
    df = pd.DataFrame([
        {"company_name": "Acme Labs", "location": "Austin"},
        {"company_name": "Beta Labs", "location": "Austin"},
    ])
    out = deduplicate_dataframe(df)
    assert len(out) == 2
