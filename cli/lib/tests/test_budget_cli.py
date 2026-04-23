import sys
from pathlib import Path

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
