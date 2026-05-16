#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/cli/lib/helix-common.sh"

HOOK_NAME="stop"
STOP_HOOK_INPUT_FILE="$(mktemp)"
trap 'rm -f "$STOP_HOOK_INPUT_FILE"' EXIT
cat >"$STOP_HOOK_INPUT_FILE" || true

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
  HELIX_AUDIT_ACTOR="stop.sh" \
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

record_session_telemetry() {
  local db_path=""
  local tool_uses="${HELIX_TOOL_USES:-${CLAUDE_TOOL_USES:-${TOOL_USES:-}}}"
  local tokens_total="${HELIX_TOKENS_TOTAL:-${CLAUDE_TOKENS_TOTAL:-${TOKENS_TOTAL:-}}}"
  local cost_usd="${HELIX_COST_USD:-${CLAUDE_COST_USD:-${COST_USD:-}}}"
  db_path="$(resolve_db_path)" || return 0

  HELIX_SESSION_TELEMETRY_DB_PATH="$db_path" \
  HELIX_SESSION_TELEMETRY_INPUT_PATH="$STOP_HOOK_INPUT_FILE" \
  HELIX_SESSION_TELEMETRY_FALLBACK_SESSION_ID="${HELIX_SESSION_ID:-}" \
  HELIX_SESSION_TELEMETRY_FALLBACK_TOOL_USES="$tool_uses" \
  HELIX_SESSION_TELEMETRY_FALLBACK_TOKENS="$tokens_total" \
  HELIX_SESSION_TELEMETRY_FALLBACK_COST="$cost_usd" \
  python3 - <<'PY'
import json
import os
import sys
from pathlib import Path


def warn(message: str) -> None:
    sys.stderr.write(f"WARNING: stop hook telemetry skipped: {message}\n")


def load_payload(path_text: str) -> dict:
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warn(f"stdin is not valid JSON ({exc})")
        return {}
    if not isinstance(data, dict):
        warn("stdin JSON root must be an object")
        return {}
    return data


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


def parse_non_negative_int(value, field_name: str) -> int:
    if value in (None, ""):
        return 0
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative integer")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, float) and value.is_integer():
        parsed = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        parsed = int(text)
    elif isinstance(value, dict):
        for key in ("total", "total_tokens", "tokens_total"):
            if key in value:
                return parse_non_negative_int(value[key], field_name)
        raise ValueError(f"{field_name} must be a non-negative integer")
    else:
        raise ValueError(f"{field_name} must be a non-negative integer")
    if parsed < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return parsed


def parse_tool_uses(value) -> int:
    if isinstance(value, list):
        return len(value)
    return parse_non_negative_int(value, "tool_uses")


def parse_non_negative_float(value, field_name: str) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative number")
    if isinstance(value, (int, float)):
        parsed = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return 0.0
        parsed = float(text)
    elif isinstance(value, dict):
        for key in ("total", "cost_usd", "usd"):
            if key in value:
                return parse_non_negative_float(value[key], field_name)
        raise ValueError(f"{field_name} must be a non-negative number")
    else:
        raise ValueError(f"{field_name} must be a non-negative number")
    if parsed < 0:
        raise ValueError(f"{field_name} must be a non-negative number")
    return parsed


payload = load_payload(os.environ.get("HELIX_SESSION_TELEMETRY_INPUT_PATH", ""))
session_id_value = find_first(payload, {"session_id"})
session_id = (
    str(session_id_value).strip()
    if session_id_value not in (None, "")
    else os.environ.get("HELIX_SESSION_TELEMETRY_FALLBACK_SESSION_ID", "").strip()
)
if not session_id:
    warn("session_id missing")
    raise SystemExit(0)

tool_uses_value = find_first(payload, {"tool_uses"})
tokens_value = find_first(payload, {"tokens", "tokens_total"})
cost_value = find_first(payload, {"cost", "cost_usd"})

tool_uses = parse_tool_uses(
    tool_uses_value
    if tool_uses_value is not None
    else os.environ.get("HELIX_SESSION_TELEMETRY_FALLBACK_TOOL_USES", "")
)
tokens_total = parse_non_negative_int(
    tokens_value
    if tokens_value is not None
    else os.environ.get("HELIX_SESSION_TELEMETRY_FALLBACK_TOKENS", ""),
    "tokens_total",
)
cost_usd = parse_non_negative_float(
    cost_value
    if cost_value is not None
    else os.environ.get("HELIX_SESSION_TELEMETRY_FALLBACK_COST", ""),
    "cost_usd",
)

helix_home = Path(os.environ["HELIX_HOME"])
sys.path.insert(0, str(helix_home / "cli" / "lib"))

import helix_db  # type: ignore


try:
    with helix_db._write_connection(os.environ["HELIX_SESSION_TELEMETRY_DB_PATH"]) as conn:
        helix_db.upsert_session_telemetry(
            conn,
            session_id,
            actor="stop.sh",
            tool_uses_count=tool_uses,
            tokens_total=tokens_total,
            cost_usd=cost_usd,
            ended=True,
        )
except Exception as exc:
    warn(str(exc))
PY
}

record_hook_audit >/dev/null 2>&1 || true
record_session_telemetry || true
