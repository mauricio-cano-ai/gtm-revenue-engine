import pytest
from pydantic import ValidationError

from gtm_engine.models import ProspectRecord


def test_prospect_requires_company_identity():
    with pytest.raises(ValidationError, match="company identity"):
        ProspectRecord(person_name="Ada Lovelace")


def test_domain_is_normalized_on_model_input():
    record = ProspectRecord(company_name="Acme", domain="https://www.Acme.com/path")
    assert record.domain == "acme.com"


def test_signal_values_are_clamped_to_unit_interval():
    record = ProspectRecord(
        company_name="Acme",
        firmographic_fit=1.4,
        intent_signal=-0.2,
    )
    assert record.firmographic_fit == 1.0
    assert record.intent_signal == 0.0
