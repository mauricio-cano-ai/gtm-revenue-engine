from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from .models import ProspectRecord, ScoreBreakdown


def load_scoring_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    weights = config.get("weights", {})
    if sum(int(value) for value in weights.values()) != 100:
        raise ValueError("scoring weights must sum to 100")
    return config


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def score_prospect(
    record: ProspectRecord,
    config: Mapping[str, Any],
    now: datetime | None = None,
) -> ScoreBreakdown:
    current = _as_utc(now or datetime.now(timezone.utc))
    weights = config["weights"]
    freshness_days = config.get("freshness_days", {})
    stale_multiplier = float(config.get("stale_multiplier", 0.35))

    components: dict[str, int] = {}
    reasons: list[str] = []

    for signal_name, max_points_raw in weights.items():
        max_points = int(max_points_raw)
        signal_value = float(getattr(record, signal_name, 0.0) or 0.0)
        multiplier = 1.0
        timestamp_field = f"{signal_name}_at"
        timestamp = getattr(record, timestamp_field, None)
        max_age_days = freshness_days.get(signal_name)

        if signal_value > 0 and timestamp is not None and max_age_days is not None:
            age_days = max(0, (current - _as_utc(timestamp)).days)
            if age_days > int(max_age_days):
                multiplier = stale_multiplier
                reasons.append(
                    f"{signal_name} stale ({age_days}d > {max_age_days}d); "
                    f"applied {stale_multiplier:.2f} freshness multiplier"
                )
        points = int(round(max_points * signal_value * multiplier))
        points = max(0, min(max_points, points))
        components[signal_name] = points
        if points and multiplier == 1.0:
            reasons.append(f"{signal_name}: {points}/{max_points}")

    total = max(0, min(100, sum(components.values())))
    return ScoreBreakdown(total=total, components=components, reasons=reasons)
