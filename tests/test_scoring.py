from datetime import datetime, timedelta, timezone
from pathlib import Path

from gtm_engine.models import ProspectRecord
from gtm_engine.scoring import load_scoring_config, score_prospect


CONFIG = load_scoring_config(Path("config/scoring.yaml"))


def test_perfect_fit_scores_100():
    now = datetime(2026, 9, 13, tzinfo=timezone.utc)
    record = ProspectRecord(
        company_name="Perfect Co",
        firmographic_fit=1,
        technographic_fit=1,
        hiring_signal=1,
        funding_signal=1,
        intent_signal=1,
        behavioral_signal=1,
        hiring_signal_at=now,
        funding_signal_at=now,
        intent_signal_at=now,
        behavioral_signal_at=now,
    )
    score = score_prospect(record, CONFIG, now=now)
    assert score.total == 100
    assert score.components["intent_signal"] == 20


def test_empty_signals_score_zero():
    record = ProspectRecord(company_name="Quiet Co")
    score = score_prospect(record, CONFIG, now=datetime(2026, 9, 13, tzinfo=timezone.utc))
    assert score.total == 0


def test_stale_signal_is_discounted():
    now = datetime(2026, 9, 13, tzinfo=timezone.utc)
    record = ProspectRecord(
        company_name="Old Intent Co",
        intent_signal=1,
        intent_signal_at=now - timedelta(days=60),
    )
    score = score_prospect(record, CONFIG, now=now)
    assert score.components["intent_signal"] == 7
    assert any("stale" in reason.lower() for reason in score.reasons)
