#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/cli/lib/helix-common.sh"

HOOK_NAME="post-tool-use"

resolve_db_path() {
  HELIX_DB_LIB_DIR="$HELIX_HOME/cli/lib" \
  HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
  python3 - <<'PY'
import os
import sys

sys.path.insert(0, os.environ["HELIX_DB_LIB_DIR"])
import helix_db  # type: ignore

print(helix_db.resolve_default_db_path())
PY
}

record_hook_audit() {
  local db_path=""
  local automation_run_id="${HELIX_AUTOMATION_RUN_ID:-}"
  local tool_uses="${HELIX_TOOL_USES:-${CLAUDE_TOOL_USES:-${TOOL_USES:-}}}"
  local duration_ms="${HELIX_HOOK_DURATION_MS:-${CLAUDE_HOOK_DURATION_MS:-${HOOK_DURATION_MS:-}}}"
  db_path="$(resolve_db_path)" || return 0

  HELIX_AUDIT_DB_PATH="$db_path" \
  HELIX_AUDIT_ACTOR="post-tool-use.sh" \
  HELIX_AUDIT_HOOK_NAME="$HOOK_NAME" \
  HELIX_AUDIT_TOOL_USES="$tool_uses" \
  HELIX_AUDIT_DURATION_MS="$duration_ms" \
  HELIX_AUDIT_RUN_ID="$automation_run_id" \
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
run_id = parse_optional_int(os.environ.get("HELIX_AUDIT_RUN_ID", ""))
payload = {key: value for key, value in payload.items() if value is not None}

with helix_db._write_connection(os.environ["HELIX_AUDIT_DB_PATH"]) as conn:
    helix_db.insert_audit_log(
        conn,
        audit_kind="hook_exec",
        actor=os.environ["HELIX_AUDIT_ACTOR"],
        run_id=run_id,
        payload=payload,
    )
PY
}

record_hook_audit >/dev/null 2>&1 || true
