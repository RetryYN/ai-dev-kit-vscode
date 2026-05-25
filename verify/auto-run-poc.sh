#!/bin/bash
set -euo pipefail
# verify/auto-run-poc.sh — L7-auto-run-poc-session-cleanerplan.md negative case fail-close 検証
# 契約: PoC PLAN §2 scope #3 4 negative case fail-close

TEST_NAME="verify/auto-run-poc.sh"
PASS_COUNT=0
FAIL_COUNT=0
FAIL_DETAIL=()

HELIX_HOME="${HELIX_HOME:-$(pwd)}"
CLI="$HELIX_HOME/cli"
TMP_ROOT="$(mktemp -d /tmp/helix-auto-run-poc-XXXXXX)"
trap 'rm -rf "$TMP_ROOT"' EXIT

PROJECT_ROOT="$TMP_ROOT/project"
FAKE_BIN="$TMP_ROOT/bin"
HANDOVER_JSON="$TMP_ROOT/handover.json"
BUDGET_JSON="$TMP_ROOT/budget.json"

mkdir -p "$PROJECT_ROOT" "$FAKE_BIN"

assert_eq() {
  local actual="$1"
  local expected="$2"
  local label="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "PASS: $label"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL: $label (expected=$expected actual=$actual)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_DETAIL+=("$label: expected=$expected actual=$actual")
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "PASS: $label"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL: $label (missing=$needle)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_DETAIL+=("$label: missing=$needle")
  fi
}

write_scheduler_stub() {
  cat >"$FAKE_BIN/helix" <<EOF
#!/usr/bin/env bash
set -euo pipefail
if [[ "\${1:-}" == "handover" && "\${2:-}" == "status" && "\${3:-}" == "--json" ]]; then
  cat "$HANDOVER_JSON"
  exit 0
fi
if [[ "\${1:-}" == "budget" && "\${2:-}" == "status" && "\${3:-}" == "--json" ]]; then
  cat "$BUDGET_JSON"
  exit 0
fi
echo "unexpected helix args: \$*" >&2
exit 2
EOF
  chmod +x "$FAKE_BIN/helix"
}

write_budget_json() {
  cat >"$BUDGET_JSON" <<'JSON'
{"claude":{"weekly_remaining_pct":70},"codex":{"weekly_used_pct":20},"recommendations":[]}
JSON
}

json_get() {
  local path="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -r "$path"
    return
  fi
  python3 -c 'import json, sys
path = sys.argv[1].strip()
payload = json.load(sys.stdin)
if not path.startswith("."):
    raise SystemExit(f"unsupported json path: {path}")
value = payload
for part in path[1:].split("."):
    value = value[part]
if isinstance(value, bool):
    print(str(value).lower())
elif value is None:
    print("null")
else:
    print(value)' "$path"
}

echo "=== $TEST_NAME ==="

write_scheduler_stub
write_budget_json

# Case 1: carry_count==0 → no-op
printf '%s\n' '{"files":{"pending_count":0}}' >"$HANDOVER_JSON"
case1="$(
  PATH="$FAKE_BIN:$CLI:/usr/bin:/bin" \
  HELIX_HOME="$HELIX_HOME" \
  HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
  "$CLI/helix-heartbeat-scheduler" --json | json_get '.should_schedule'
)"
assert_eq "$case1" "false" "C1 carry_count==0 should_schedule=false"

# Case 2: bg_task_active==True → no-op
printf '%s\n' '{"files":{"pending_count":3}}' >"$HANDOVER_JSON"
case2="$(
  PATH="$FAKE_BIN:$CLI:/usr/bin:/bin" \
  HELIX_HOME="$HELIX_HOME" \
  HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
  HELIX_BG_TASK_ACTIVE=1 \
  "$CLI/helix-heartbeat-scheduler" --json | json_get '.should_schedule'
)"
assert_eq "$case2" "false" "C2 bg_task_active should_schedule=false"

# Case 3: budget window expired → resume action='idle' + reason='budget window expired'
PATH="$FAKE_BIN:$CLI:/usr/bin:/bin" \
HELIX_HOME="$HELIX_HOME" \
HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
"$CLI/helix-auto-run" start --plan-id TEST --duration-minutes 1 >/dev/null

python3 - "$PROJECT_ROOT/.helix/auto-run/current.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["budget_window"]["deadline_at"] = "1990-01-01T00:00:00+09:00"
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

case3_json="$(
  PATH="$FAKE_BIN:$CLI:/usr/bin:/bin" \
  HELIX_HOME="$HELIX_HOME" \
  HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
  "$CLI/helix-auto-run" resume --json
)"
case3_action="$(printf '%s' "$case3_json" | json_get '.resume.action')"
case3_reason="$(printf '%s' "$case3_json" | json_get '.resume.reason')"
assert_eq "$case3_action|$case3_reason" "idle|budget window expired" "C3 expired budget idle with reason"

# Case 4: max_restart_count exceeded → session_cleaner.preflight().blockers に 'max_restart_exceeded' 含む
if [[ ! -f "$CLI/lib/session_cleaner.py" ]]; then
  echo "SKIP: C4 TODO: session_cleaner W2-A 完成後 enable"
else
  mkdir -p "$PROJECT_ROOT/.helix/auto-run"
  cat >"$PROJECT_ROOT/.helix/auto-run/session.json" <<'JSON'
{"restart_count":5,"max_restart_count":5}
JSON
  case4="$(
    PYTHONPATH="$HELIX_HOME" python3 - "$PROJECT_ROOT" <<'PY'
import sys
from cli.lib.session_cleaner import SessionCleaner

print(SessionCleaner(project_root=sys.argv[1]).preflight())
PY
  )"
  assert_contains "$case4" "max_restart_exceeded" "C4 max_restart_count exceeded blocks preflight"
fi

if [[ $FAIL_COUNT -gt 0 ]]; then
  printf 'FAIL DETAIL:\n'
  printf ' - %s\n' "${FAIL_DETAIL[@]}"
  echo "FAIL: $FAIL_COUNT cases"
  exit 1
fi

echo "PASS: $PASS_COUNT/4 cases"
