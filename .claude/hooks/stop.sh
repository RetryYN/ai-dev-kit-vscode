#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/cli/lib/helix-common.sh"

HOOK_NAME="stop"

record_invocation_telemetry() {
  local db_path="${HELIX_DIR}/helix.db"
  local parent_invocation_id=""
  local payload=""
  local row_id=""

  if [[ "${HELIX_PARENT_INVOCATION_ID:-}" =~ ^[0-9]+$ ]]; then
    parent_invocation_id="${HELIX_PARENT_INVOCATION_ID}"
  fi

  payload="$(
    HELIX_INVOCATION_TYPE="hook" \
    HELIX_INVOCATION_ROLE="" \
    HELIX_INVOCATION_MODEL="" \
    HELIX_INVOCATION_TASK_ID="$HOOK_NAME" \
    HELIX_INVOCATION_PARENT_ID="$parent_invocation_id" \
    HELIX_INVOCATION_HOOK_NAME="$HOOK_NAME" \
    HELIX_INVOCATION_HOOK_PATH="$SCRIPT_DIR/stop.sh" \
    python3 - <<'PY'
import json
import os


payload = {
    "type": os.environ["HELIX_INVOCATION_TYPE"],
    "role": None,
    "model": None,
    "task_id": os.environ.get("HELIX_INVOCATION_TASK_ID") or None,
    "parent_invocation_id": int(os.environ["HELIX_INVOCATION_PARENT_ID"])
    if os.environ.get("HELIX_INVOCATION_PARENT_ID", "").isdigit()
    else None,
}
payload["raw_meta"] = {
    "hook_name": os.environ.get("HELIX_INVOCATION_HOOK_NAME") or None,
    "hook_path": os.environ.get("HELIX_INVOCATION_HOOK_PATH") or None,
}
print(json.dumps(payload, ensure_ascii=False))
PY
  )" || return 0

  row_id="$(python3 "$HELIX_HOME/cli/lib/helix_db.py" record-invocation "$db_path" "$payload" 2>/dev/null)" || return 0
  if [[ "$row_id" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$row_id"
  fi
}

record_hook_audit() {
  local db_path="${HELIX_DIR}/helix.db"
  local invocation_log_id="${1:-}"
  local tool_uses="${HELIX_TOOL_USES:-${CLAUDE_TOOL_USES:-${TOOL_USES:-}}}"
  local duration_ms="${HELIX_HOOK_DURATION_MS:-${CLAUDE_HOOK_DURATION_MS:-${HOOK_DURATION_MS:-}}}"

  HELIX_AUDIT_DB_PATH="$db_path" \
  HELIX_AUDIT_ACTOR="stop.sh" \
  HELIX_AUDIT_HOOK_NAME="$HOOK_NAME" \
  HELIX_AUDIT_TOOL_USES="$tool_uses" \
  HELIX_AUDIT_DURATION_MS="$duration_ms" \
  HELIX_AUDIT_INVOCATION_ID="$invocation_log_id" \
  python3 - <<'PY'
import json
import os
import sys
from pathlib import Path


def parse_optional_int(raw: str) -> int | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    return None


def parse_optional_value(raw: str):
    value = (raw or "").strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


helix_home = Path(os.environ["HELIX_HOME"])
sys.path.insert(0, str(helix_home / "cli" / "lib"))

import helix_db  # type: ignore


payload = {
    "hook_name": os.environ.get("HELIX_AUDIT_HOOK_NAME") or None,
    "tool_uses": parse_optional_value(os.environ.get("HELIX_AUDIT_TOOL_USES", "")),
    "duration_ms": parse_optional_int(os.environ.get("HELIX_AUDIT_DURATION_MS", "")),
}
invocation_log_id = parse_optional_int(os.environ.get("HELIX_AUDIT_INVOCATION_ID", ""))
if invocation_log_id is not None:
    payload["invocation_log_id"] = invocation_log_id
payload = {key: value for key, value in payload.items() if value is not None}

with helix_db._write_connection(os.environ["HELIX_AUDIT_DB_PATH"]) as conn:
    helix_db.insert_audit_log(
        conn,
        audit_kind="hook_exec",
        actor=os.environ["HELIX_AUDIT_ACTOR"],
        run_id=None,
        payload=payload,
    )
PY
}

invocation_log_id="$(record_invocation_telemetry || true)"
record_hook_audit "$invocation_log_id" >/dev/null 2>&1 || true
