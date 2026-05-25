"""Session cleaner PoC for HELIX auto-run.

契約: docs/plans/L7/L7-auto-run-poc-session-cleanerplan.md
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

try:
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from paths import project_root as detect_project_root


STATE_PATH = Path(".helix") / "auto-run" / "session.json"
AUTO_RUN_STATE_PATH = Path(".helix") / "auto-run" / "current.json"
BG_TASK_ACTIVE_PATH = Path(".helix") / "auto-run" / "bg_task_active"
HANDOVER_CURRENT_PATH = Path(".helix") / "handover" / "CURRENT.md"
STATE_VERSION = 1


class SessionCleanerError(RuntimeError):
    """Raised when session cleaner state or arguments are invalid."""


class ClaudeAdapter(Protocol):
    def start(self, session_name: str) -> None: ...

    def terminate(self, session_name: str) -> None: ...


class TmuxAdapter(Protocol):
    def new_session(self, name: str, command: str) -> None: ...

    def kill_session(self, name: str) -> None: ...


class FakeClaudeAdapter:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.terminated: list[str] = []

    def start(self, session_name: str) -> None:
        self.started.append(session_name)

    def terminate(self, session_name: str) -> None:
        self.terminated.append(session_name)


class FakeTmuxAdapter:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, str]] = {}

    def new_session(self, name: str, command: str) -> None:
        self.sessions[name] = {"command": command}

    def kill_session(self, name: str) -> None:
        self.sessions.pop(name, None)


def _now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


class SessionCleaner:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        claude_adapter: ClaudeAdapter | None = None,
        tmux_adapter: TmuxAdapter | None = None,
        dry_run: bool = True,
        max_restart_count: int = 5,
    ) -> None:
        if max_restart_count < 0:
            raise SessionCleanerError("max_restart_count must be >= 0")
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.state_path = self.project_root / STATE_PATH
        self.auto_run_state_path = self.project_root / AUTO_RUN_STATE_PATH
        self.handover_path = self.project_root / HANDOVER_CURRENT_PATH
        self.bg_task_active_path = self.project_root / BG_TASK_ACTIVE_PATH
        self.claude_adapter = claude_adapter or FakeClaudeAdapter()
        self.tmux_adapter = tmux_adapter or FakeTmuxAdapter()
        self.dry_run = dry_run
        self.max_restart_count = max_restart_count

    def _default_state(self) -> dict[str, Any]:
        return {
            "version": STATE_VERSION,
            "restart_count": 0,
            "last_restart_at": None,
            "last_old_session": None,
            "last_new_session": None,
        }

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise SessionCleanerError(f"invalid session cleaner state: {exc}") from exc
        if not isinstance(payload, dict):
            raise SessionCleanerError("invalid session cleaner state")
        state = self._default_state()
        state.update(payload)
        state["restart_count"] = int(state.get("restart_count") or 0)
        return state

    def _save_state(self, payload: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.state_path.parent / f"{self.state_path.name}.tmp.{os.getpid()}"
        tmp_path.write_text(_json_dump(payload), encoding="utf-8")
        os.replace(tmp_path, self.state_path)

    def _budget_ok(self) -> bool:
        if not self.auto_run_state_path.exists():
            return True
        try:
            payload = json.loads(self.auto_run_state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        if not isinstance(payload, dict):
            return False
        budget_window = payload.get("budget_window") or {}
        deadline_at = str(budget_window.get("deadline_at") or "").strip()
        if not deadline_at:
            return True
        try:
            return datetime.fromisoformat(deadline_at) > datetime.now().astimezone()
        except ValueError:
            return False

    def _bg_task_active(self) -> bool:
        if self.bg_task_active_path.exists():
            return True
        raw = os.environ.get("HELIX_AUTO_RUN_BG_TASK_ACTIVE", "").strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def _handover_ok(self) -> tuple[bool, str | None]:
        if not self.handover_path.exists():
            return False, "handover_missing"
        if not os.access(self.handover_path.parent, os.W_OK):
            return False, "handover_unwritable"
        return True, None

    def _preflight_from_state(self, state: dict[str, Any]) -> dict[str, Any]:
        blockers: list[str] = []
        handover_ok, handover_blocker = self._handover_ok()
        if handover_blocker:
            blockers.append(handover_blocker)

        budget_ok = self._budget_ok()
        if not budget_ok:
            blockers.append("budget_expired")

        restart_count_ok = int(state["restart_count"]) < self.max_restart_count
        if not restart_count_ok:
            blockers.append("max_restart_exceeded")

        if self._bg_task_active():
            blockers.append("bg_task_active")

        return {
            "ready": not blockers,
            "blockers": blockers,
            "handover_ok": handover_ok,
            "budget_ok": budget_ok,
            "restart_count_ok": restart_count_ok,
        }

    def preflight(self) -> dict[str, Any]:
        return self._preflight_from_state(self._load_state())

    def restart(self) -> dict[str, Any]:
        state = self._load_state()
        preflight = self._preflight_from_state(state)
        next_count = int(state["restart_count"]) + 1
        old_session = str(state.get("last_new_session") or "session-current")
        new_session = f"session-cleaner-{next_count}"
        if not preflight["ready"]:
            reason = preflight["blockers"][0] if preflight["blockers"] else "preflight_failed"
            return {
                "status": "blocked",
                "old_session": state.get("last_new_session"),
                "new_session": new_session,
                "restart_count": int(state["restart_count"]),
                "reason": reason,
            }

        if self.dry_run:
            return {
                "status": "dry_run",
                "old_session": old_session,
                "new_session": new_session,
                "restart_count": next_count,
                "reason": "dry_run",
            }

        self.claude_adapter.terminate(old_session)
        self.tmux_adapter.kill_session(old_session)
        self.tmux_adapter.new_session(new_session, "claude --continue")
        self.claude_adapter.start(new_session)

        updated_state = {
            "version": STATE_VERSION,
            "restart_count": next_count,
            "last_restart_at": _now_iso(),
            "last_old_session": old_session,
            "last_new_session": new_session,
        }
        self._save_state(updated_state)
        return {
            "status": "restarted",
            "old_session": old_session,
            "new_session": new_session,
            "restart_count": next_count,
            "reason": "restarted",
        }

    def reset(self) -> dict[str, Any]:
        payload = self._default_state()
        self._save_state(payload)
        return payload
