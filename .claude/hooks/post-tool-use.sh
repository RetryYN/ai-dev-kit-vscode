#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/cli/lib/helix-common.sh"

HOOK_NAME="post-tool-use"

record_invocation_telemetry() {
  local db_path="${HELIX_DIR}/helix.db"
  local parent_invocation_id=""
  local payload=""

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
    HELIX_INVOCATION_HOOK_PATH="$SCRIPT_DIR/post-tool-use.sh" \
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

  python3 "$PROJECT_ROOT/cli/lib/helix_db.py" record-invocation "$db_path" "$payload" >/dev/null 2>&1 || true
}

record_invocation_telemetry || true
