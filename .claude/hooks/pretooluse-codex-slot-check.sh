#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TMP_INPUT="$(mktemp)"
trap 'rm -f "$TMP_INPUT"' EXIT
DB_PATH="${HELIX_DB_PATH:-$PROJECT_ROOT/.helix/helix.db}"
export HELIX_DB_PATH="$DB_PATH"

cat >"$TMP_INPUT" 2>/dev/null || true
[[ -s "$TMP_INPUT" ]] || printf '{}' >"$TMP_INPUT"

read_hook_field() {
  local field="$1"
  python3 - "$field" "$TMP_INPUT" <<'PY' 2>/dev/null || true
import json
import sys

field = sys.argv[1]
path = sys.argv[2]
with open(path, "r", encoding="utf-8") as fh:
    payload = json.load(fh)

tool_input = payload.get("tool_input") or {}
values = {
    "tool_name": payload.get("tool_name") or "",
    "command": tool_input.get("command") or "",
}
print(values.get(field, ""))
PY
}

tool_name="$(read_hook_field tool_name)"
[[ "$tool_name" == "Bash" ]] || exit 0

tool_input="$(read_hook_field command)"
case "$tool_input" in
  *"helix codex"*|*"helix-codex"*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT_ROOT" 2>/dev/null || exit 0
active="$(timeout 3 python3 -c 'from cli.lib import agent_slots; print(len(agent_slots.list_active_slots()))' 2>/dev/null || echo 0)"

if [[ "$active" =~ ^[0-9]+$ ]] && [[ "$active" -ge 6 ]]; then
  cat <<EOF >&2
<system-reminder>
[harness] 現在 active slot=$active、8 並列ルールに近い。
新規 Codex 投入前に依存判定 (ファイル衝突 / 後段依存 / 共有状態) を再確認してください。
</system-reminder>
EOF
  ACTIVE_COUNT="$active" timeout 2 python3 - <<'PY' 2>/dev/null || true
import os
from cli.lib import harness_monitor

harness_monitor.record_event(
    "push",
    "slot_count_warning",
    severity="warning",
    payload={"active": int(os.environ["ACTIVE_COUNT"])},
    user_visible=True,
)
PY
fi

if [[ "$tool_input" == *"--wbs-id"* && "$tool_input" != *"--reference-doc"* ]]; then
  cat <<'EOF' >&2
<system-reminder>
[harness] --wbs-id 指定時は --reference-doc も必要 (helix codex は task-plan.yaml を lookup 対象外)。
</system-reminder>
EOF
  timeout 2 python3 - <<'PY' 2>/dev/null || true
from cli.lib import harness_monitor

harness_monitor.record_event(
    "push",
    "wbs_id_without_reference",
    severity="warning",
    payload={},
    user_visible=True,
)
PY
fi

exit 0
