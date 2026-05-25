import io
import sys
from pathlib import Path
from contextlib import redirect_stdout

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import budget_cli


def test_main_dispatches_status_subcommand(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_cmd(args) -> int:
        captured["subcmd"] = args.subcmd
        captured["json"] = args.json
        captured["no_cache"] = args.no_cache
        captured["forecast"] = args.forecast
        captured["since_hours"] = args.since_hours
        return 11

    monkeypatch.setattr(budget_cli, "cmd_status", fake_cmd)

    result = budget_cli.main(["status", "--json", "--no-cache", "--forecast", "--since-hours", "12"])

    assert result == 11
    assert captured == {
        "subcmd": "status",
        "json": True,
        "no_cache": True,
        "forecast": True,
        "since_hours": 12.0,
    }


def test_main_dispatches_cache_subcommand(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_cmd(args) -> int:
        captured["subcmd"] = args.subcmd
        captured["cache_action"] = args.cache_action
        return 7

    monkeypatch.setattr(budget_cli, "cmd_cache", fake_cmd)

    result = budget_cli.main(["cache", "clear"])

    assert result == 7
    assert captured == {"subcmd": "cache", "cache_action": "clear"}


def test_main_exits_non_zero_for_invalid_args() -> None:
    with pytest.raises(SystemExit) as exc_info:
        budget_cli.main(["set-limit"])

    assert exc_info.value.code == 2


def test_format_with_block_info() -> None:
    result = {
        "claude": {
            "plan": "max",
            "weekly_used_pct": 60,
            "weekly_remaining_pct": 40,
            "weekly_cost_usd": 120.37,
            "weekly_budget_usd": 200,
            "source": "ccusage",
            "block_cost_usd": 9.17,
            "block_burn_per_hour": 9.45,
            "block_projected_cost": 47.21,
            "block_remaining_minutes": 240,
            "block_end_time": "2025-05-10T15:00:00Z",
        },
        "codex": {
            "plan": "max",
            "five_hour_used_pct": 42,
            "weekly_used_pct": 67,
            "source": "state.db",
        },
        "recommendations": [],
    }

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=False)

    assert buf.getvalue().splitlines() == [
        "Claude (weekly ref $200): 60% used / 40% remaining ($120.37 of $200, source: ccusage)",
        "Claude (5h block):        $9.17 used | burn $9.45/h | proj $47.21 | 4h0m remaining (source: ccusage blocks)",
        "  [note] $200 weekly は helix の reference budget。Anthropic 公式 weekly quota とは異なる",
        "  [note] ccusage cost と Anthropic UI 表示は別 metric (cache/session weight 差)、UI 値は console.anthropic.com で確認",
        "Codex  (max): 42% (5h) / 67% (weekly)  (source: state.db)",
    ]


def test_format_with_block_info_includes_ui_divergence_note() -> None:
    result = {
        "claude": {
            "plan": "max",
            "weekly_used_pct": 60,
            "weekly_remaining_pct": 40,
            "weekly_cost_usd": 120.37,
            "weekly_budget_usd": 200,
            "source": "ccusage",
            "block_cost_usd": 9.17,
            "block_burn_per_hour": 9.45,
            "block_projected_cost": 47.21,
            "block_remaining_minutes": 240,
            "block_end_time": "2025-05-10T15:00:00Z",
        },
        "codex": {
            "plan": "max",
            "five_hour_used_pct": 42,
            "weekly_used_pct": 67,
            "source": "state.db",
        },
        "recommendations": [],
    }

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=False)

    lines = buf.getvalue().splitlines()
    assert any(
        "console.anthropic.com" in line or "UI 値は" in line
        for line in lines
    )


def test_format_without_block_info() -> None:
    result = {
        "claude": {
            "plan": "max",
            "weekly_used_pct": 57,
            "weekly_remaining_pct": 43,
            "weekly_cost_usd": 114.0,
            "weekly_budget_usd": 200,
            "source": "ccusage",
        },
        "codex": {
            "plan": "max",
            "five_hour_used_pct": 42,
            "weekly_used_pct": 67,
            "source": "state.db",
        },
        "recommendations": [],
    }

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=False)

    assert buf.getvalue().splitlines() == [
        "Claude (weekly ref $200): 57% used / 43% remaining ($114.00 of $200, source: ccusage)",
        "Codex  (max): 42% (5h) / 67% (weekly)  (source: state.db)",
    ]


def test_status_with_forecast_flag_outputs_forecast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = {
        "claude": {
            "weekly_used_pct": 50,
            "block_remaining_minutes": 120,
            "source": "ccusage",
        },
        "codex": {"plan": "max", "five_hour_used_pct": 42, "weekly_used_pct": 67, "source": "state.db"},
        "recommendations": [],
    }

    monkeypatch.setattr(
        budget_cli,
        "forecast_exhaustion",
        lambda **_: {
            "projected_exhaustion_hours": 24.0,
            "projected_exhaustion_date": "2026-05-25T00:00:00+00:00",
            "rate_per_hour": 1.0,
            "on_track": False,
        },
    )

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=False, include_forecast=True)

    assert "forecast (weekly): projected exhaustion in 24h (off track)" in buf.getvalue()


def test_status_without_forecast_flag_omits_forecast() -> None:
    result = {
        "claude": {
            "weekly_used_pct": 50,
            "block_remaining_minutes": 120,
            "source": "ccusage",
        },
        "codex": {"plan": "max", "five_hour_used_pct": 42, "weekly_used_pct": 67, "source": "state.db"},
        "recommendations": [],
    }

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=False, include_forecast=False)

    assert "forecast" not in buf.getvalue()


def test_budget_cli_json_output() -> None:
    result = {
        "claude": {
            "source": "ccusage",
            "weekly_used_pct": 60,
            "weekly_remaining_pct": 40,
            "block_remaining_minutes": 180,
        },
        "codex": {
            "source": "state.db",
            "five_hour_used_pct": 25,
            "weekly_used_pct": 70,
        },
        "recommendations": [],
        "cached": False,
    }

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=True, include_forecast=False)

    payload = __import__("json").loads(buf.getvalue())
    assert payload["summary"]["claude"] == {
        "source": "ccusage",
        "used_pct": 60,
        "remaining": 40,
    }
    assert payload["summary"]["codex"] == {
        "source": "state.db",
        "used_pct": 70,
        "remaining": 30,
    }
    assert payload["per_source_breakdown"]["claude_weekly"] == {
        "source": "ccusage",
        "used_pct": 60,
        "remaining": 40,
    }
    assert payload["per_source_breakdown"]["codex_five_hour"] == {
        "source": "state.db",
        "used_pct": 25,
        "remaining": 75,
    }


def test_budget_cli_json_with_forecast(monkeypatch: pytest.MonkeyPatch) -> None:
    result = {
        "claude": {
            "source": "ccusage",
            "weekly_used_pct": 50,
            "weekly_remaining_pct": 50,
            "block_remaining_minutes": 120,
        },
        "codex": {
            "source": "state.db",
            "five_hour_used_pct": 20,
            "weekly_used_pct": 35,
        },
        "recommendations": [],
        "cached": False,
    }
    forecast = {
        "projected_exhaustion_hours": 24.0,
        "projected_exhaustion_date": "2026-05-25T00:00:00+00:00",
        "rate_per_hour": 1.0,
        "on_track": False,
    }
    monkeypatch.setattr(
        budget_cli,
        "_build_weekly_forecast",
        lambda _claude, since_hours=None: forecast,
    )

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(result, as_json=True, include_forecast=True)

    payload = __import__("json").loads(buf.getvalue())
    assert payload["forecast"] == forecast
    assert payload["claude"]["weekly_forecast"] == forecast


def test_budget_cli_forecast_respects_since_hours(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = {
        "claude": {
            "weekly_used_pct": 50,
            "block_remaining_minutes": 120,
            "source": "ccusage",
        },
        "codex": {"plan": "max", "five_hour_used_pct": 42, "weekly_used_pct": 67, "source": "state.db"},
        "recommendations": [],
    }
    captured: dict[str, float] = {}

    def fake_forecast_exhaustion(**kwargs):
        captured["elapsed_hours"] = kwargs["elapsed_hours"]
        return {
            "projected_exhaustion_hours": 24.0,
            "projected_exhaustion_date": "2026-05-25T00:00:00+00:00",
            "rate_per_hour": 1.0,
            "on_track": False,
        }

    monkeypatch.setattr(budget_cli, "forecast_exhaustion", fake_forecast_exhaustion)

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(
            result,
            as_json=False,
            include_forecast=True,
            since_hours=12.0,
        )

    assert captured["elapsed_hours"] == 12.0
    assert "forecast (weekly): projected exhaustion in 24h (off track)" in buf.getvalue()


def test_budget_cli_forecast_since_hours_with_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = {
        "claude": {
            "source": "ccusage",
            "weekly_used_pct": 50,
            "weekly_remaining_pct": 50,
            "block_remaining_minutes": 120,
        },
        "codex": {
            "source": "state.db",
            "five_hour_used_pct": 20,
            "weekly_used_pct": 35,
        },
        "recommendations": [],
        "cached": False,
    }
    captured: dict[str, float] = {}

    def fake_forecast_exhaustion(**kwargs):
        captured["elapsed_hours"] = kwargs["elapsed_hours"]
        return {
            "projected_exhaustion_hours": 10.0,
            "projected_exhaustion_date": "2026-05-25T00:00:00+00:00",
            "rate_per_hour": 5.0,
            "on_track": True,
        }

    monkeypatch.setattr(budget_cli, "forecast_exhaustion", fake_forecast_exhaustion)

    buf = io.StringIO()
    with redirect_stdout(buf):
        budget_cli._print_status(
            result,
            as_json=True,
            include_forecast=True,
            since_hours=6.0,
        )

    payload = __import__("json").loads(buf.getvalue())
    assert captured["elapsed_hours"] == 6.0
    assert payload["forecast"]["projected_exhaustion_hours"] == 10.0
