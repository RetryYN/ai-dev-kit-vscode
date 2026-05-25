from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from budget_forecast import forecast_exhaustion


def test_forecast_exhaustion_on_track() -> None:
    """DoD 検証: L7-budget-forecastplan on-track 判定."""
    result = forecast_exhaustion(
        current_used_pct=10,
        elapsed_hours=24,
        period_hours=168,
    )

    assert result["rate_per_hour"] == 10 / 24
    assert result["on_track"] is True
    assert result["projected_exhaustion_hours"] == 216
    assert isinstance(datetime.fromisoformat(result["projected_exhaustion_date"]), datetime)


def test_forecast_exhaustion_off_track() -> None:
    """DoD 検証: L7-budget-forecastplan off-track 判定."""
    result = forecast_exhaustion(
        current_used_pct=50,
        elapsed_hours=24,
        period_hours=168,
    )

    assert result["rate_per_hour"] == 50 / 24
    assert result["on_track"] is False
    assert result["projected_exhaustion_hours"] == 24
    assert isinstance(datetime.fromisoformat(result["projected_exhaustion_date"]), datetime)


def test_forecast_exhaustion_zero_elapsed() -> None:
    """DoD 検証: L7-budget-forecastplan elapsed_hours=0 の退避動作."""
    result = forecast_exhaustion(
        current_used_pct=50,
        elapsed_hours=0,
        period_hours=168,
    )

    assert result["rate_per_hour"] == 0.0
    assert result["projected_exhaustion_hours"] is None
    assert result["projected_exhaustion_date"] is None
