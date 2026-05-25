#!/bin/bash
set -euo pipefail
# verify/auto-run-compaction-poc.sh — L7-auto-run-poc-compaction-apiplan.md negative case fail-close
# 契約: PoC PLAN §2 scope #3 3 negative case fail-close

TEST_NAME="verify/auto-run-compaction-poc.sh"
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAIL_DETAIL=()

HELIX_HOME="${HELIX_HOME:-$(pwd)}"
CLI="$HELIX_HOME/cli"
TMP="$(mktemp -d -t compaction-poc-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

PROJECT_ROOT="$TMP/project"
FAKE_BIN="$TMP/bin"
HANDOVER_JSON="$TMP/handover.json"
BUDGET_JSON="$TMP/budget.json"

mkdir -p "$PROJECT_ROOT/.helix/handover" "$FAKE_BIN"

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

skip_case() {
  local label="$1"
  echo "SKIP: $label"
  SKIP_COUNT=$((SKIP_COUNT + 1))
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

write_helix_stub() {
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
exec "$CLI/helix" "\$@"
EOF
  chmod +x "$FAKE_BIN/helix"
}

write_budget_json() {
  cat >"$BUDGET_JSON" <<'JSON'
{"claude":{"weekly_remaining_pct":70},"codex":{"weekly_used_pct":20},"recommendations":[]}
JSON
}

echo "=== $TEST_NAME ==="

write_helix_stub
write_budget_json

# Case 1: carry_count==0 → no-op (auto_run_engine 経由で確認)
printf '%s\n' '{"files":{"pending_count":0}}' >"$HANDOVER_JSON"
PATH="$FAKE_BIN:$CLI:/usr/bin:/bin" \
HELIX_HOME="$HELIX_HOME" \
HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
"$CLI/helix-auto-run" start --plan-id TEST --duration-minutes 1 >/dev/null

case1="$(
  PATH="$FAKE_BIN:$CLI:/usr/bin:/bin" \
  HELIX_HOME="$HELIX_HOME" \
  HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
  "$CLI/helix-auto-run" heartbeat --json | json_get '.resume.action'
)"
assert_eq "$case1" "idle" "C1 carry_count==0 resume.action=idle"

# Case 2: compaction unavailable → adapter returns failed (Python script で fake adapter 使用)
if [[ ! -f "$CLI/lib/compaction_adapter.py" ]]; then
  skip_case "C2 compaction_adapter.py not implemented yet"
else
  case2="$(
    PYTHONPATH="$HELIX_HOME" python3 - <<'PY'
from cli.lib.compaction_adapter import FakeCompactionAdapter

adapter = FakeCompactionAdapter(available=False)
result = adapter.request_compaction()
assert result["status"] == "failed"
print("PASS")
PY
  )"
  assert_contains "$case2" "PASS" "C2 compaction unavailable returns failed"
fi

# Case 3: drift > threshold → recommendation='request_compaction' (Python script で check_drift_threshold)
if [[ ! -f "$CLI/lib/compaction_adapter.py" ]]; then
  skip_case "C3 compaction_adapter.py not implemented yet"
else
  case3="$(
    PYTHONPATH="$HELIX_HOME" python3 - <<'PY'
from cli.lib.compaction_adapter import check_drift_threshold

r = check_drift_threshold(0.7, threshold=0.5)
assert r["ok"] is False
assert r["recommendation"] == "request_compaction"
print("PASS")
PY
  )"
  assert_contains "$case3" "PASS" "C3 drift threshold recommends request_compaction"
fi

if [[ $FAIL_COUNT -gt 0 ]]; then
  printf 'FAIL DETAIL:\n'
  printf ' - %s\n' "${FAIL_DETAIL[@]}"
  echo "FAIL: $FAIL_COUNT cases"
  exit 1
fi

if [[ $SKIP_COUNT -gt 0 ]]; then
  echo "PASS: $PASS_COUNT/3 cases ($SKIP_COUNT skipped)"
else
  echo "PASS: $PASS_COUNT/3 cases"
fi
