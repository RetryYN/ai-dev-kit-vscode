"""Compaction adapter PoC for HELIX auto-run.

契約: docs/plans/L7/L7-auto-run-poc-compaction-apiplan.md
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

try:
    from .concurrent_lock import file_lock
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from concurrent_lock import file_lock
    from paths import project_root as detect_project_root


STATE_PATH = Path(".helix") / "auto-run" / "compaction.json"
HANDOVER_CURRENT_PATH = Path(".helix") / "handover" / "CURRENT.json"
HANDOVER_SYNC_PATH = Path(".helix") / "handover" / "COMPACTION-SYNC.json"
STATE_VERSION = 1
LOCK_NAME = "auto-run-compaction-state"
DEFAULT_BEFORE_TOKENS = 1000
MAX_NEXT_ACTION_SUMMARY = 200


class CompactionError(RuntimeError):
    """Raised when compaction state or arguments are invalid."""


class CompactionAdapter(Protocol):
    def request_compaction(self) -> dict[str, Any]: ...

    def get_compaction_status(self) -> dict[str, Any]: ...


def _now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _resolve_project_root() -> Path:
    return Path(detect_project_root()).expanduser().resolve()


def _validate_ratio(value: float, *, label: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise CompactionError(f"{label} must be a float between 0.0 and 1.0") from exc
    if normalized < 0.0 or normalized > 1.0:
        raise CompactionError(f"{label} must be between 0.0 and 1.0")
    return normalized


def _default_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "last_compaction_at": None,
        "compaction_count": 0,
        "last_drift": None,
    }


def _state_path() -> Path:
    return _resolve_project_root() / STATE_PATH


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return _default_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise CompactionError(f"invalid compaction state: {exc}") from exc
    if not isinstance(payload, dict):
        raise CompactionError("invalid compaction state")
    state = _default_state()
    state.update(payload)
    state["compaction_count"] = int(state.get("compaction_count") or 0)
    last_drift = state.get("last_drift")
    state["last_drift"] = None if last_drift is None else _validate_ratio(last_drift, label="last_drift")
    return state


def _write_state_file(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.parent / f"{path.name}.tmp.{os.getpid()}"
    tmp_path.write_text(_json_dump(payload), encoding="utf-8")
    os.replace(tmp_path, path)


def _truncate_summary(value: str, *, limit: int = MAX_NEXT_ACTION_SUMMARY) -> str:
    text = " ".join(value.split()).strip()
    return text[:limit]


def _handover_next_action_summary(payload: dict[str, Any]) -> str:
    next_action = payload.get("next_action")
    if isinstance(next_action, str) and next_action.strip():
        return _truncate_summary(next_action)

    next_actions = payload.get("next_actions")
    if isinstance(next_actions, list):
        joined = "; ".join(str(item).strip() for item in next_actions if str(item).strip())
        if joined:
            return _truncate_summary(joined)
    return ""


def _read_handover_snapshot(project_root: Path) -> dict[str, Any]:
    handover_path = project_root / HANDOVER_CURRENT_PATH
    if not handover_path.exists():
        return {
            "exists": False,
            "updated_at": None,
            "next_action_summary": "",
        }

    try:
        payload = json.loads(handover_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    updated_at = payload.get("updated_at")
    return {
        "exists": True,
        "updated_at": str(updated_at) if updated_at else None,
        "next_action_summary": _handover_next_action_summary(payload),
    }


def _persist_success(*, compacted_at: str) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_dir = _resolve_project_root() / ".helix" / "locks"
    # Keep writes serialized and atomic so later waves can reuse the same state safely.
    with file_lock(LOCK_NAME, lock_dir=lock_dir):
        state = _default_state()
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:  # pragma: no cover
                raise CompactionError(f"invalid compaction state: {exc}") from exc
            if not isinstance(payload, dict):
                raise CompactionError("invalid compaction state")
            state.update(payload)
        state["version"] = STATE_VERSION
        state["last_compaction_at"] = compacted_at
        state["compaction_count"] = int(state.get("compaction_count") or 0) + 1
        state["last_drift"] = 0.0
        _write_state_file(path, state)


class FakeCompactionAdapter:
    def __init__(self, *, available: bool = True, simulated_drift: float = 0.2) -> None:
        self.requests: list[dict[str, Any]] = []
        self.available = available
        self.simulated_drift = _validate_ratio(simulated_drift, label="simulated_drift")
        self.last_compaction_at: str | None = None

    def request_compaction(self) -> dict[str, Any]:
        requested_at = _now_iso()
        self.requests.append(
            {
                "requested_at": requested_at,
                "available": self.available,
                "simulated_drift": self.simulated_drift,
            }
        )
        if not self.available:
            return {
                "status": "failed",
                "compacted_at": None,
                "before_tokens": None,
                "after_tokens": None,
            }

        before_tokens = DEFAULT_BEFORE_TOKENS
        after_tokens = max(1, int(round(before_tokens * (1.0 - self.simulated_drift))))
        self.last_compaction_at = requested_at
        _persist_success(compacted_at=requested_at)
        return {
            "status": "success",
            "compacted_at": requested_at,
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
        }

    def get_compaction_status(self) -> dict[str, Any]:
        state = _load_state()
        return {
            "available": self.available,
            "last_compaction_at": self.last_compaction_at or state["last_compaction_at"],
            "estimated_drift": self.simulated_drift,
        }


class DryRunCompactionAdapter:
    """実呼び出しなし、log のみ。production safe."""

    def __init__(self) -> None:
        self.log: list[str] = []

    def request_compaction(self) -> dict[str, Any]:
        self.log.append(f"{_now_iso()} request_compaction dry_run")
        return {
            "status": "dry_run",
            "compacted_at": None,
            "before_tokens": None,
            "after_tokens": None,
        }

    def get_compaction_status(self) -> dict[str, Any]:
        self.log.append(f"{_now_iso()} get_compaction_status dry_run")
        return {
            "available": True,
            "last_compaction_at": None,
            "estimated_drift": 0.0,
        }


def check_drift_threshold(drift: float, threshold: float = 0.5) -> dict[str, Any]:
    """
    Returns: {'ok': bool, 'drift': float, 'threshold': float, 'recommendation': str}
    drift > threshold → recommendation='request_compaction'
    drift <= threshold → recommendation='continue'
    """

    normalized_drift = _validate_ratio(drift, label="drift")
    normalized_threshold = _validate_ratio(threshold, label="threshold")
    ok = normalized_drift <= normalized_threshold
    return {
        "ok": ok,
        "drift": normalized_drift,
        "threshold": normalized_threshold,
        "recommendation": "continue" if ok else "request_compaction",
    }


def sync_handover_after_compaction(
    adapter: CompactionAdapter,
    *,
    project_root: Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Run compaction, then return or persist a compact handover snapshot."""
    compaction_status = adapter.request_compaction()
    handover_snapshot = _read_handover_snapshot(project_root)
    if not handover_snapshot["exists"]:
        return {
            "compaction_status": compaction_status,
            "handover_snapshot": handover_snapshot,
            "status": "no_handover",
        }

    if dry_run:
        return {
            "compaction_status": compaction_status,
            "handover_snapshot": handover_snapshot,
            "status": "dry_run",
        }

    sync_path = project_root / HANDOVER_SYNC_PATH
    sync_path.parent.mkdir(parents=True, exist_ok=True)
    _write_state_file(sync_path, handover_snapshot)
    return {
        "compaction_status": compaction_status,
        "handover_snapshot": handover_snapshot,
        "status": "synced",
    }
