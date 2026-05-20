#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$REPO_ROOT}"

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT
cat >"$payload_file" || true

if ! python3 - "$payload_file" "$PROJECT_ROOT" <<'PY'
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def truthy_env(*names: str) -> bool:
    for name in names:
        value = os.environ.get(name, "").strip().lower()
        if value and value not in {"0", "false", "no", "off"}:
            return True
    return False


def load_payload(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def find_first(value, names: set[str]):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in names:
                return child
        for child in value.values():
            result = find_first(child, names)
            if result is not None:
                return result
    elif isinstance(value, list):
        for child in value:
            result = find_first(child, names)
            if result is not None:
                return result
    return None


def detect_session_id(payload: dict) -> str:
    for name in ("HELIX_SESSION_ID", "CLAUDE_SESSION_ID", "SESSION_ID"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    payload_session_id = find_first(payload, {"session_id"})
    if payload_session_id not in (None, ""):
        return str(payload_session_id).strip()
    return "unknown-session"


def handover_stale(project_root: Path, now_epoch: int) -> bool:
    handover_path = project_root / ".helix" / "handover" / "CURRENT.json"
    if not handover_path.exists():
        return False
    try:
        payload = json.loads(handover_path.read_text(encoding="utf-8"))
        updated_at = str(payload.get("updated_at") or "").strip()
        if not updated_at:
            return False
        updated_epoch = int(datetime.fromisoformat(updated_at).timestamp())
    except Exception:
        return False
    return now_epoch - updated_epoch > 300


def state_persist_failed(project_root: Path, now_epoch: int) -> bool:
    exit_code = os.environ.get("HELIX_LAST_STATE_PERSIST_EXIT_CODE", "").strip()
    if exit_code and exit_code not in {"0"}:
        return True
    if truthy_env("HELIX_PRECOMPACT_STATE_PERSIST_FAILED", "HELIX_STATE_PERSIST_FAILED"):
        return True
    return handover_stale(project_root, now_epoch)


def read_blocked_sessions(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def append_blocked_session(path: Path, session_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{session_id}\n")


def write_backup(backup_dir: Path, session_id: str, payload: dict[str, object]) -> str:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"precompact-state-{session_id}-{stamp}.json"
    backup_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(backup_path)


payload = load_payload(Path(os.sys.argv[1]))
project_root = Path(os.sys.argv[2]).resolve(strict=False)
session_id = detect_session_id(payload)
now_epoch = int(os.environ.get("HELIX_PRECOMPACT_NOW_EPOCH", str(int(time.time()))))
unsaved_decisions = truthy_env("HELIX_UNSAVED_DECISIONS")
persist_failed = state_persist_failed(project_root, now_epoch)

blocked_sessions_file = Path(
    os.environ.get(
        "HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE",
        str(Path(os.environ.get("HOME", "~")).expanduser() / ".helix" / "precompact_blocked_sessions"),
    )
).expanduser()
blocked_sessions = read_blocked_sessions(blocked_sessions_file)
one_shot_consumed = session_id in blocked_sessions

if persist_failed and unsaved_decisions and not one_shot_consumed:
    append_blocked_session(blocked_sessions_file, session_id)
    print(
        json.dumps(
            {
                "decision": "block",
                "message": "PreCompact blocked once: state persistence failed and unsaved decisions remain",
                "sessionId": session_id,
                "conditions": {
                    "persist_failed": True,
                    "unsaved_decisions": True,
                    "one_shot_consumed": False,
                },
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)

backup_dir = Path(
    os.environ.get(
        "HELIX_PRECOMPACT_BACKUP_DIR",
        str(project_root / ".helix" / "backups" / "precompact"),
    )
).expanduser()
manual_compact = truthy_env("HELIX_PRECOMPACT_MANUAL", "HELIX_MANUAL_COMPACT")
backup_path = write_backup(
    backup_dir,
    session_id,
    {
        "session_id": session_id,
        "unsaved_decisions": unsaved_decisions,
        "persist_failed": persist_failed,
        "one_shot_consumed": one_shot_consumed,
        "manual_compact": manual_compact,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    },
)

message = "PreCompact: state backed up, compaction proceeding"
if manual_compact:
    message += " (manual /compact respected)"

print(
    json.dumps(
        {
            "decision": "continue",
            "message": message,
            "backup": backup_path,
            "sessionId": session_id,
            "conditions": {
                "persist_failed": persist_failed,
                "unsaved_decisions": unsaved_decisions,
                "one_shot_consumed": one_shot_consumed,
            },
        },
        ensure_ascii=False,
    )
)
PY
then
  python3 - <<'PY'
import json
print(json.dumps({"decision": "continue", "message": "PreCompact: fail-open fallback"}, ensure_ascii=False))
PY
fi

exit 0
