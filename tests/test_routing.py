from pathlib import Path

from gtm_engine.routing import route_score
from gtm_engine.scoring import load_scoring_config


CONFIG = load_scoring_config(Path("config/scoring.yaml"))


def test_tier_boundaries():
    assert route_score(80, CONFIG).tier == "A"
    assert route_score(79, CONFIG).tier == "B"
    assert route_score(60, CONFIG).tier == "B"
    assert route_score(59, CONFIG).tier == "C"
    assert route_score(40, CONFIG).tier == "C"
    assert route_score(39, CONFIG).tier == "LOW"


def test_route_includes_action_and_owner():
    decision = route_score(91, CONFIG)
    assert decision.action == "immediate_sales_routing"
    assert decision.owner == "senior_ae_queue"
