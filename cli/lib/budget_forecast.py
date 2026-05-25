"""budget_forecast.py — budget exhaustion forecast helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def forecast_exhaustion(
    *,
    current_used_pct: float,
    elapsed_hours: float,
    period_hours: float = 168,
) -> dict[str, Any]:
    elapsed = float(elapsed_hours)
    used_pct = float(current_used_pct)
    rate_per_hour = 0.0
    projected_exhaustion_hours: float | None = None
    projected_exhaustion_date: str | None = None

    if elapsed > 0:
        rate_per_hour = used_pct / elapsed

    if rate_per_hour > 0:
        remaining_pct = 100.0 - used_pct
        projected_exhaustion_hours = remaining_pct / rate_per_hour
        projected_exhaustion_date = (
            datetime.now(timezone.utc) + timedelta(hours=projected_exhaustion_hours)
        ).isoformat()

    remaining_period_hours = float(period_hours) - elapsed
    on_track = (
        projected_exhaustion_hours is None
        or projected_exhaustion_hours >= remaining_period_hours
    )

    return {
        "projected_exhaustion_hours": projected_exhaustion_hours,
        "projected_exhaustion_date": projected_exhaustion_date,
        "rate_per_hour": rate_per_hour,
        "on_track": on_track,
    }
