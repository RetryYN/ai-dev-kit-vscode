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
        return 11

    monkeypatch.setattr(budget_cli, "cmd_status", fake_cmd)

    result = budget_cli.main(["status", "--json", "--no-cache"])

    assert result == 11
    assert captured == {"subcmd": "status", "json": True, "no_cache": True}


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
