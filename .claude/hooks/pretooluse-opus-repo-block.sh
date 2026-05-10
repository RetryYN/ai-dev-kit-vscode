#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELIX_ROOT="$(cd "$script_dir/../.." && pwd)"

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

case "${file_path:-}" in
  "$HELIX_ROOT/.helix"/*|"$HELIX_ROOT/.helix")
    exit 0
    ;;
  "$HELIX_ROOT"/*)
    is_repo_path=1
    ;;
  *)
    case "${file_path:-}" in
      "$HOME"/.claude/projects/*/memory/*)
        exit 0
        ;;
    esac
    ;;
esac

if [[ "${HELIX_SUPPRESS_HOOK:-0}" == "1" ]]; then
  exit 0
fi

if [[ "${HELIX_ALLOW_OPUS_REPO_EDIT:-0}" == "1" && -n "${HELIX_OPUS_EDIT_REASON:-}" ]]; then
  exit 0
fi

if [[ "${HELIX_ALLOW_OPUS_PLAN_FIX:-0}" == "1" && "$file_path" =~ (^|/)docs/plans/PLAN-[^/]+\.md$ ]]; then
  exit 0
fi

if [[ "$is_repo_path" -eq 0 ]]; then
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
  python3 - "$reason" <<'PY'
import json
import sys

reason = sys.argv[1]
payload = {"blocked": True, "reason": reason}
sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
PY
  exit 2
fi

exit 0
