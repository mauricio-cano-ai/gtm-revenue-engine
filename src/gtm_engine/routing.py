from __future__ import annotations

from typing import Any, Mapping

from .models import RoutingDecision


def route_score(score: int, config: Mapping[str, Any]) -> RoutingDecision:
    thresholds = config["thresholds"]
    if score >= int(thresholds["tier_a"]):
        key, tier = "tier_a", "A"
    elif score >= int(thresholds["tier_b"]):
        key, tier = "tier_b", "B"
    elif score >= int(thresholds["tier_c"]):
        key, tier = "tier_c", "C"
    else:
        key, tier = "low", "LOW"
    route = config["routing"][key]
    return RoutingDecision(tier=tier, action=route["action"], owner=route["owner"])
