#!/usr/bin/env bash
# PLAN-083 Phase 2: Agent tool 呼び出し自動 fire (agent_slots 記録)
# Claude Code PreToolUse hook (matcher=Agent) から呼ばれる
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 0

# stdin JSON から tool_name + tool_input を読む
input=$(cat 2>/dev/null || echo "{}")

tool_name=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get("tool_name", ""))
except Exception:
    print("")
' 2>/dev/null || echo "")

# Agent tool 以外は無視 (exit 0)
[[ "$tool_name" != "Agent" ]] && exit 0

# subagent_type 抽出
subagent_type=$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("subagent_type", "") or "")
except Exception:
    print("")
' 2>/dev/null || echo "")

# subagent_type 不明な場合は skip
[[ -z "$subagent_type" ]] && exit 0

# session_id 検出 (session_helper.py 使用、なければ env 直接読み)
session_id=$(timeout 3 python3 -m cli.lib.session_helper 2>/dev/null || echo "")
if [[ -z "$session_id" ]]; then
  session_id="${HELIX_SESSION_ID:-unknown-noenv}"
fi

# agent_slots に fire (記録失敗時も session 阻害禁止)
timeout 3 python3 -c "
import sys
from cli.lib import agent_slots
agent_slots.fire_slot(
    agent_kind='claude_subagent',
    subagent_type=sys.argv[1],
    session_id=sys.argv[2],
    slot_source='pretooluse_hook',
)
" "$subagent_type" "$session_id" >/dev/null 2>&1 || true

# system-reminder (debug 用、HELIX_HARNESS_DEBUG=1 時のみ)
if [[ "${HELIX_HARNESS_DEBUG:-0}" == "1" ]]; then
  cat <<EOF >&2
[harness] Agent fire: subagent_type=$subagent_type session_id=$session_id
EOF
fi

exit 0
