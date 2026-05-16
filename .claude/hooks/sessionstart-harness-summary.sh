#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT" 2>/dev/null || exit 0

stale_count="$(timeout 3 python3 -c 'from cli.lib import agent_slots; print(len(agent_slots.list_stale_slots(threshold_minutes=5)))' 2>/dev/null || echo 0)"
if [[ "$stale_count" =~ ^[0-9]+$ ]] && [[ "$stale_count" -gt 0 ]]; then
  cat <<EOF
[harness] 前 session の release 漏れ slot: $stale_count 件
  → helix agent slots --stale で詳細確認
EOF
fi

critical_count="$(timeout 3 python3 -c 'from cli.lib import harness_monitor; print(len(harness_monitor.list_recent_events(days=1, severity="critical")))' 2>/dev/null || echo 0)"
if [[ "$critical_count" =~ ^[0-9]+$ ]] && [[ "$critical_count" -gt 0 ]]; then
  cat <<EOF
[harness] 直近 24h の critical event: $critical_count 件
EOF
fi

exit 0
