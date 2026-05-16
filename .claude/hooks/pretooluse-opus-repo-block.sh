#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELIX_ROOT="$(cd "$script_dir/../.." && pwd)"
project_root="${CLAUDE_PROJECT_DIR:-$HELIX_ROOT}"

tmp_input="$(mktemp)"
trap 'rm -f "$tmp_input"' EXIT
cat >"$tmp_input"

read_json_field() {
  local expr="$1"
  python3 - "$expr" "$tmp_input" <<'PY'
import json
import sys

expr = sys.argv[1]
path = sys.argv[2]
with open(path, "r", encoding="utf-8") as fh:
    payload = json.load(fh)

tool_input = payload.get("tool_input") or {}
values = {
    "tool_name": payload.get("tool_name") or "",
    "file_path": tool_input.get("file_path") or payload.get("file_path") or "",
}
print(values.get(expr, ""))
PY
}

tool_name="$(read_json_field tool_name)"
file_path="$(read_json_field file_path)"

is_repo_path=0
allow_repo_state=0

record_audit_events() {
  local gate_verdict="$1"
  HELIX_PROJECT_ROOT="$project_root" \
  HELIX_AUDIT_ACTOR="pretooluse-opus-repo-block.sh" \
  HELIX_AUDIT_HOOK_NAME="pretooluse-opus-repo-block" \
  HELIX_AUDIT_TOOL_NAME="$tool_name" \
  HELIX_AUDIT_FILE_PATH="$file_path" \
  HELIX_AUDIT_GATE_VERDICT="$gate_verdict" \
  HELIX_AUDIT_REASON="${reason:-}" \
  python3 - "$HELIX_ROOT" <<'PY'
import os
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import helix_db  # type: ignore

db_path = helix_db.resolve_default_db_path()

def parse_optional_int(raw: str) -> int | None:
    value = (raw or "").strip()
    if value.isdigit():
        return int(value)
    return None

run_id = parse_optional_int(os.environ.get("HELIX_AUTOMATION_RUN_ID", ""))

hook_payload = {
    "hook_name": os.environ.get("HELIX_AUDIT_HOOK_NAME") or None,
    "tool_name": os.environ.get("HELIX_AUDIT_TOOL_NAME") or None,
    "file_path": os.environ.get("HELIX_AUDIT_FILE_PATH") or None,
}
hook_payload = {key: value for key, value in hook_payload.items() if value is not None}

gate_payload = dict(hook_payload)
gate_payload["gate_name"] = "opus_repo_edit_policy"
gate_payload["verdict"] = os.environ.get("HELIX_AUDIT_GATE_VERDICT") or None
reason = os.environ.get("HELIX_AUDIT_REASON") or None
if reason:
    gate_payload["reason"] = reason
gate_payload = {key: value for key, value in gate_payload.items() if value is not None}

with helix_db._write_connection(db_path) as conn:
    helix_db.insert_audit_log(
        conn,
        audit_kind="hook_exec",
        actor=os.environ["HELIX_AUDIT_ACTOR"],
        run_id=run_id,
        payload=hook_payload,
    )
    helix_db.insert_audit_log(
        conn,
        audit_kind="gate_eval",
        actor=os.environ["HELIX_AUDIT_ACTOR"],
        run_id=run_id,
        payload=gate_payload,
    )
PY
}

case "${file_path:-}" in
  "$HELIX_ROOT/.helix"/*|"$HELIX_ROOT/.helix")
    record_audit_events "bypassed" >/dev/null 2>&1 || true
    exit 0
    ;;
  "$HELIX_ROOT"/*)
    is_repo_path=1
    ;;
  *)
    case "${file_path:-}" in
      "$HOME"/.claude/projects/*/memory/*)
        record_audit_events "bypassed" >/dev/null 2>&1 || true
        exit 0
        ;;
    esac
    ;;
esac

if [[ "${HELIX_SUPPRESS_HOOK:-0}" == "1" ]]; then
  record_audit_events "suppressed" >/dev/null 2>&1 || true
  exit 0
fi

if [[ "${HELIX_ALLOW_OPUS_REPO_EDIT:-0}" == "1" && -n "${HELIX_OPUS_EDIT_REASON:-}" ]]; then
  record_audit_events "allowed" >/dev/null 2>&1 || true
  exit 0
fi

if [[ "${HELIX_ALLOW_OPUS_PLAN_FIX:-0}" == "1" && "$file_path" =~ (^|/)docs/plans/PLAN-[^/]+\.md$ ]]; then
  record_audit_events "allowed" >/dev/null 2>&1 || true
  exit 0
fi

if [[ "$is_repo_path" -eq 0 ]]; then
  record_audit_events "bypassed" >/dev/null 2>&1 || true
  exit 0
fi

reason="PM (Opus) は repo file を直接 Edit/Write できません。helix codex --role <pg|se|docs> --task ... で委譲してください"

if [[ "$tool_name" == "Edit" || "$tool_name" == "Write" || "$tool_name" == "MultiEdit" ]]; then
  if [[ "${HELIX_AUDIT_OPUS_BLOCK:-0}" == "1" ]]; then
    mkdir -p "$HELIX_ROOT/.helix/audit"
    python3 - "$HELIX_ROOT/.helix/audit/opus-block-events.log" "$tool_name" "$file_path" "$reason" <<'PY'
import json
import sys
from datetime import datetime, timezone

log_file, tool_name, file_path, reason = sys.argv[1:5]
event = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tool_name": tool_name,
    "file_path": file_path,
    "reason": reason,
}
with open(log_file, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(event, ensure_ascii=False) + "\n")
PY
  fi
  record_audit_events "blocked" >/dev/null 2>&1 || true
  python3 - "$reason" <<'PY'
import json
import sys

reason = sys.argv[1]
payload = {"blocked": True, "reason": reason}
sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
PY
  exit 2
fi

record_audit_events "allowed" >/dev/null 2>&1 || true
exit 0
