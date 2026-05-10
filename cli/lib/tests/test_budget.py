import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import budget


class _RunResult:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout


def _weekly_payload(cost: float = 120.37, tokens: int = 12345) -> str:
    return json.dumps({
        "weekly": [
            {
                "totalCost": cost,
                "totalTokens": tokens,
            }
        ]
    })


def test_budget_cache_round_trip_with_filesystem(tmp_path: Path) -> None:
    cache = budget.BudgetCache(tmp_path / "cache", ttl_sec=60)

    cache.set("status", {"ok": True, "count": 2})
    loaded = cache.get("status")

    assert loaded is not None
    assert loaded["ok"] is True
    assert loaded["count"] == 2
    assert loaded["_cache_age_sec"] >= 0


def test_budget_cache_expires_old_entries(tmp_path: Path) -> None:
    cache = budget.BudgetCache(tmp_path / "cache", ttl_sec=1)
    cache.set("status", {"ok": True})
    cache_file = tmp_path / "cache" / "status.json"
    old_ts = time.time() - 120
    os.utime(cache_file, (old_ts, old_ts))

    assert cache.get("status") is None


def test_claude_budget_uses_jsonl_fallback(tmp_path: Path, monkeypatch) -> None:
    # ccusage が PATH にあると ccusage source が優先される
    # (本テストは ccusage 不在時の jsonl-fallback 経路を検証する目的)
    monkeypatch.setattr(budget.shutil, "which", lambda _: None)

    projects_dir = tmp_path / ".claude" / "projects" / "sample"
    projects_dir.mkdir(parents=True)
    (projects_dir / "usage.jsonl").write_text("one\ntwo\nthree\n", encoding="utf-8")

    result = budget.ClaudeBudget.get(home=tmp_path)

    assert result["source"] == "jsonl-fallback"
    assert result["approx_line_count"] == 3
    assert result["weekly_used_pct"] == 0
    assert result["weekly_remaining_pct"] == 100


def test_block_info_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(budget.shutil, "which", lambda _: "/usr/bin/ccusage")

    calls: list[list[str]] = []

    def fake_run(cmd, capture_output, text, timeout):  # noqa: ANN001
        calls.append(cmd)
        if cmd[1] == "weekly":
            return _RunResult(0, _weekly_payload())
        if cmd[1] == "blocks":
            return _RunResult(0, json.dumps({
                "blocks": [
                    {"isActive": False},
                    {
                        "isActive": True,
                        "costUSD": 9.174,
                        "burnRate": {"costPerHour": 9.445},
                        "projection": {"totalCost": 47.214, "remainingMinutes": 240},
                        "endTime": "2025-05-10T15:00:00Z",
                    },
                ]
            }))
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(budget.subprocess, "run", fake_run)

    result = budget.ClaudeBudget.get(home=Path("/tmp"))

    assert calls == [["/usr/bin/ccusage", "weekly", "--json"], ["/usr/bin/ccusage", "blocks", "--json"]]
    assert result["weekly_used_pct"] == 60
    assert result["weekly_remaining_pct"] == 40
    assert result["weekly_cost_usd"] == 120.37
    assert result["block_cost_usd"] == 9.17
    assert result["block_burn_per_hour"] == 9.45
    assert result["block_projected_cost"] == 47.21
    assert result["block_remaining_minutes"] == 240
    assert result["block_end_time"] == "2025-05-10T15:00:00Z"


def test_block_info_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(budget.shutil, "which", lambda _: "/usr/bin/ccusage")

    calls: list[list[str]] = []

    def fake_run(cmd, capture_output, text, timeout):  # noqa: ANN001
        calls.append(cmd)
        if cmd[1] == "weekly":
            return _RunResult(0, _weekly_payload())
        if cmd[1] == "blocks":
            return _RunResult(1, "")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(budget.subprocess, "run", fake_run)

    result = budget.ClaudeBudget.get(home=Path("/tmp"))

    assert calls == [["/usr/bin/ccusage", "weekly", "--json"], ["/usr/bin/ccusage", "blocks", "--json"]]
    assert result["weekly_used_pct"] == 60
    assert result["weekly_remaining_pct"] == 40
    assert "block_cost_usd" not in result
    assert "block_burn_per_hour" not in result
    assert "block_projected_cost" not in result
    assert "block_remaining_minutes" not in result
    assert "block_end_time" not in result


def test_codex_budget_reads_rollout_state_from_sqlite(tmp_path: Path) -> None:
    state_dir = tmp_path / ".codex"
    state_dir.mkdir(parents=True)
    state_db = state_dir / "state.db"
    conn = sqlite3.connect(state_db)
    try:
        conn.execute("CREATE TABLE rollout_state (five_hour_pct INTEGER, weekly_pct INTEGER)")
        conn.execute("INSERT INTO rollout_state (five_hour_pct, weekly_pct) VALUES (?, ?)", (42, 67))
        conn.commit()
    finally:
        conn.close()

    result = budget.CodexBudget.get(home=tmp_path)

    assert result == {
        "plan": "max",
        "five_hour_used_pct": 42,
        "weekly_used_pct": 67,
        "by_model": {},
        "source": "state.db",
    }


def test_collect_status_adds_recommendations_and_uses_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    calls = {"claude": 0, "codex": 0}

    def fake_claude() -> dict[str, object]:
        calls["claude"] += 1
        return {
            "plan": "max",
            "weekly_used_pct": 81,
            "weekly_remaining_pct": 19,
            "source": "fake-claude",
            "warning": "claude warning",
        }

    def fake_codex() -> dict[str, object]:
        calls["codex"] += 1
        return {
            "plan": "max",
            "five_hour_used_pct": 20,
            "weekly_used_pct": 96,
            "by_model": {},
            "source": "fake-codex",
            "warning": "codex warning",
        }

    monkeypatch.setattr(budget.ClaudeBudget, "get", staticmethod(fake_claude))
    monkeypatch.setattr(budget.CodexBudget, "get", staticmethod(fake_codex))

    first = budget.collect_status(use_cache=True)
    second = budget.collect_status(use_cache=True)

    assert first["cached"] is False
    assert second["cached"] is True
    assert calls == {"claude": 1, "codex": 1}
    messages = [rec["message"] for rec in first["recommendations"]]
    severities = [rec["severity"] for rec in first["recommendations"]]
    assert "Claude 残 < 20% — 軽量タスクへの切り替え推奨" in messages
    assert "Codex 残 < 20% — 軽量タスクへの切り替え推奨" in messages
    assert "claude warning" in messages
    assert "codex warning" in messages
    assert "warning" in severities
    assert "critical" in severities
    cache_file = tmp_path / ".helix" / "budget" / "cache" / "status.json"
    assert json.loads(cache_file.read_text(encoding="utf-8"))["cached"] is False
