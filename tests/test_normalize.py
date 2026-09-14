import pandas as pd

from gtm_engine.normalize import normalize_domain, normalize_dataframe, normalize_technology


def test_normalize_domain_removes_protocol_www_path_and_case():
    assert normalize_domain("HTTPS://WWW.Example.COM/about") == "example.com"


def test_normalize_technology_collapses_common_aliases():
    assert normalize_technology(" HubSpot CRM ") == "hubspot"
    assert normalize_technology("google-workspace") == "google workspace"


def test_normalize_dataframe_trims_text_and_normalizes_domains():
    df = pd.DataFrame([
        {"company_name": " Acme ", "domain": "www.Acme.com", "technologies": "HubSpot CRM; Slack"}
    ])
    out = normalize_dataframe(df)
    assert out.iloc[0]["company_name"] == "Acme"
    assert out.iloc[0]["domain"] == "acme.com"
    assert out.iloc[0]["technologies"] == ["hubspot", "slack"]
