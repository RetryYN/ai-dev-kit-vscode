"""L7-auto-run-poc-session-cleanerplan session_cleaner 単体テスト."""

from __future__ import annotations

import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import session_cleaner


def _write_handover_current(project_root: Path) -> None:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.md"
    handover_path.parent.mkdir(parents=True, exist_ok=True)
    handover_path.write_text("# current handover\n", encoding="utf-8")


def _write_session_state(project_root: Path, *, restart_count: int) -> None:
    state_path = project_root / ".helix" / "auto-run" / "session.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "version": 1,
                "restart_count": restart_count,
                "last_restart_at": None,
                "last_old_session": "session-prev",
                "last_new_session": "session-current",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_preflight_handover_missing(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-poc-session-cleanerplan preflight blocks when handover is missing."""
    cleaner = session_cleaner.SessionCleaner(project_root=tmp_path)

    payload = cleaner.preflight()

    assert payload["ready"] is False
    assert payload["handover_ok"] is False
    assert payload["blockers"] == ["handover_missing"]


def test_preflight_runaway_guard(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-poc-session-cleanerplan preflight fail-closes on max restart count."""
    _write_handover_current(tmp_path)
    _write_session_state(tmp_path, restart_count=5)
    cleaner = session_cleaner.SessionCleaner(project_root=tmp_path, max_restart_count=5)

    payload = cleaner.preflight()

    assert payload["ready"] is False
    assert payload["restart_count_ok"] is False
    assert payload["blockers"] == ["max_restart_exceeded"]


def test_restart_success_dry_run(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-poc-session-cleanerplan dry-run restart does not touch adapters."""
    _write_handover_current(tmp_path)
    fake_claude = session_cleaner.FakeClaudeAdapter()
    fake_tmux = session_cleaner.FakeTmuxAdapter()
    cleaner = session_cleaner.SessionCleaner(
        project_root=tmp_path,
        claude_adapter=fake_claude,
        tmux_adapter=fake_tmux,
        dry_run=True,
    )

    payload = cleaner.restart()

    assert payload["status"] == "dry_run"
    assert payload["reason"] == "dry_run"
    assert fake_claude.started == []
    assert fake_claude.terminated == []
    assert fake_tmux.sessions == {}


def test_restart_calls_adapters_when_not_dry_run(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-poc-session-cleanerplan restart invokes fake adapters when allowed."""
    _write_handover_current(tmp_path)
    fake_claude = session_cleaner.FakeClaudeAdapter()
    fake_tmux = session_cleaner.FakeTmuxAdapter()
    cleaner = session_cleaner.SessionCleaner(
        project_root=tmp_path,
        claude_adapter=fake_claude,
        tmux_adapter=fake_tmux,
        dry_run=False,
    )

    payload = cleaner.restart()

    assert payload["status"] == "restarted"
    assert fake_claude.started == [payload["new_session"]]
    assert fake_claude.terminated == [payload["old_session"]]
    assert payload["new_session"] in fake_tmux.sessions
    assert payload["old_session"] not in fake_tmux.sessions


def test_restart_blocked_when_max_exceeded(tmp_path: Path) -> None:
    """DoD 検証: L7-auto-run-poc-session-cleanerplan restart blocks before adapter calls at max."""
    _write_handover_current(tmp_path)
    _write_session_state(tmp_path, restart_count=5)
    fake_claude = session_cleaner.FakeClaudeAdapter()
    fake_tmux = session_cleaner.FakeTmuxAdapter()
    cleaner = session_cleaner.SessionCleaner(
        project_root=tmp_path,
        claude_adapter=fake_claude,
        tmux_adapter=fake_tmux,
        dry_run=False,
        max_restart_count=5,
    )

    payload = cleaner.restart()

    assert payload["status"] == "blocked"
    assert payload["reason"] == "max_restart_exceeded"
    assert fake_claude.started == []
    assert fake_claude.terminated == []
    assert fake_tmux.sessions == {}
