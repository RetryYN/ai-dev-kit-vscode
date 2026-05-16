#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  TOOL_HELPER="$HELIX_ROOT/cli/tests/_helix-bats-helper.bash"
  TMP_ROOT="$(mktemp -d)"
  source "$TOOL_HELPER"
  helix_bats_mark "$TMP_ROOT"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  DB_PATH="$PROJECT_ROOT/.helix/helix.db"

  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR" "$BIN_DIR"
  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "bats@example.com"
  git config user.name "Bats"
  echo "init" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_HOME="$HELIX_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$HELIX_ROOT/cli:$PATH"
  export HELIX_DB_PATH="$DB_PATH"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"

  python3 - "$HELIX_ROOT" "$DB_PATH" >/dev/null <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db

helix_db.init_db(sys.argv[2])
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

scrum_row_json() {
  local loop_id="$1"
  python3 - "$DB_PATH" "$loop_id" <<'PY'
import json
import sqlite3
import sys

db_path, loop_id = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM scrum_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
if row is None:
    raise SystemExit(1)
print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
PY
}

create_scrum_loop() {
  local layer="$1"
  local hypothesis="$2"
  local acceptance="$3"
  local plan_id="${4:-}"

  if [[ -n "$plan_id" ]]; then
    run "$HELIX_ROOT/cli/helix-scrum" local init \
      --layer "$layer" \
      --hypothesis "$hypothesis" \
      --acceptance "$acceptance" \
      --plan-id "$plan_id"
  else
    run "$HELIX_ROOT/cli/helix-scrum" local init \
      --layer "$layer" \
      --hypothesis "$hypothesis" \
      --acceptance "$acceptance"
  fi

  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

run_scrum_poc() {
  local loop_id="$1"
  run "$HELIX_ROOT/cli/helix-scrum" local poc --loop-id "$loop_id"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

run_scrum_verify() {
  local loop_id="$1"
  run "$HELIX_ROOT/cli/helix-scrum" local verify --loop-id "$loop_id"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

run_scrum_decide() {
  local loop_id="$1"
  local result="$2"
  run "$HELIX_ROOT/cli/helix-scrum" local decide --loop-id "$loop_id" --result "$result"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

make_decided_scrum_loop() {
  local result="$1"
  local loop_id
  loop_id="$(create_scrum_loop L4 "wrap smoke ${result}" "local loop ${result}" "PLAN-079")"
  run_scrum_poc "$loop_id" >/dev/null
  run_scrum_verify "$loop_id" >/dev/null
  run_scrum_decide "$loop_id" "$result" >/dev/null
  printf '%s' "$loop_id"
}

@test "I-UPS-CLI-001: helix scrum local init creates a running loop" {
  loop_id="$(create_scrum_loop L4 "wrap smoke" "local loop created" "PLAN-079")"

  [[ "$loop_id" == H-LOCAL-* ]]

  row_json="$(scrum_row_json "$loop_id")"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["loop_id"].startswith("H-LOCAL-"), row
assert row["state"] == "S0", row
assert row["forward_layer"] == "L4", row
assert row["forward_plan_id"] == "PLAN-079", row
assert row["parent_loop_id"] is None, row
assert row["decide_result"] is None, row
assert row["related_agent_slot_id"] is None, row
assert row["started_at"], row
PY
}

@test "I-UPS-CLI-003: helix scrum local init rejects a missing layer" {
  run "$HELIX_ROOT/cli/helix-scrum" local init --hypothesis "missing layer" --acceptance "reject"

  [ "$status" -ne 0 ]
  [[ "$output" == *"Usage: helix scrum local init"* ]]
}

@test "I-UPS-CLI-004: helix scrum local init rejects an invalid forward layer" {
  run "$HELIX_ROOT/cli/helix-scrum" local init --layer LX --hypothesis "bad layer" --acceptance "reject"

  [ "$status" -ne 0 ]
  [[ "$output" == *"invalid forward_layer"* ]]
}

@test "I-UPS-CLI-005: helix scrum local list prints a stable table" {
  running_id="$(create_scrum_loop L4 "running" "running" "PLAN-079")"
  s1_id="$(create_scrum_loop L4 "s1" "s1" "PLAN-079")"
  run_scrum_poc "$s1_id" >/dev/null
  s2_id="$(create_scrum_loop L4 "s2" "s2" "PLAN-079")"
  run_scrum_poc "$s2_id" >/dev/null
  run_scrum_verify "$s2_id" >/dev/null
  finished_id="$(make_decided_scrum_loop confirmed)"

  run "$HELIX_ROOT/cli/helix-scrum" local list
  [ "$status" -eq 0 ]
  [[ "$output" =~ LOOP_ID[[:space:]]+\|[[:space:]]+LAYER[[:space:]]+\|[[:space:]]+STATE[[:space:]]+\|[[:space:]]+RESULT[[:space:]]+\|[[:space:]]+PLAN_ID[[:space:]]+\|[[:space:]]+STARTED_AT ]]
  [[ "$output" == *"$running_id"* ]]
  [[ "$output" == *"$s1_id"* ]]
  [[ "$output" == *"$s2_id"* ]]
  [[ "$output" != *"$finished_id"* ]]
}

@test "I-UPS-CLI-006: helix scrum local list --json returns active loops as JSON" {
  running_id="$(create_scrum_loop L4 "running" "running" "PLAN-079")"
  s1_id="$(create_scrum_loop L4 "s1" "s1" "PLAN-079")"
  run_scrum_poc "$s1_id" >/dev/null
  s2_id="$(create_scrum_loop L4 "s2" "s2" "PLAN-079")"
  run_scrum_poc "$s2_id" >/dev/null
  run_scrum_verify "$s2_id" >/dev/null

  run "$HELIX_ROOT/cli/helix-scrum" local list --json
  [ "$status" -eq 0 ]

  JSON_PAYLOAD="$output" python3 - "$running_id" "$s1_id" "$s2_id" <<'PY'
import json
import os
import sys

rows = json.loads(os.environ["JSON_PAYLOAD"])
assert isinstance(rows, list), rows
ids = {row["loop_id"] for row in rows}
assert {sys.argv[1], sys.argv[2], sys.argv[3]} <= ids, rows
assert all(row["state"] in {"S0", "S1", "S2"} for row in rows), rows
PY
}

@test "I-UPS-CLI-007: helix scrum local stats prints confirmed/rejected/pivot counts" {
  make_decided_scrum_loop confirmed >/dev/null
  make_decided_scrum_loop rejected >/dev/null
  make_decided_scrum_loop pivot >/dev/null

  run "$HELIX_ROOT/cli/helix-scrum" local stats
  [ "$status" -eq 0 ]
  [[ "$output" == *"CONFIRMED | REJECTED | PIVOT | TOTAL"* ]]
  [[ "$output" =~ 1[[:space:]]+\|[[:space:]]+1[[:space:]]+\|[[:space:]]+1[[:space:]]+\|[[:space:]]+3 ]]
}

@test "I-UPS-CLI-009: helix scrum local decide confirmed persists S3" {
  loop_id="$(create_scrum_loop L4 "confirmed" "confirmed" "PLAN-079")"
  run_scrum_poc "$loop_id" >/dev/null
  run_scrum_verify "$loop_id" >/dev/null
  output="$(run_scrum_decide "$loop_id" confirmed)"

  [[ "$output" == *"[scrum] $loop_id -> S3 (confirmed)"* ]]

  row_json="$(scrum_row_json "$loop_id")"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["state"] == "S3", row
assert row["decide_result"] == "confirmed", row
assert row["decided_at"], row
PY
}

@test "I-UPS-CLI-010: helix scrum local decide rejected persists S3" {
  loop_id="$(create_scrum_loop L4 "rejected" "rejected" "PLAN-079")"
  run_scrum_poc "$loop_id" >/dev/null
  run_scrum_verify "$loop_id" >/dev/null
  output="$(run_scrum_decide "$loop_id" rejected)"

  [[ "$output" == *"[scrum] $loop_id -> S3 (rejected)"* ]]

  row_json="$(scrum_row_json "$loop_id")"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["state"] == "S3", row
assert row["decide_result"] == "rejected", row
assert row["parent_loop_id"] is None, row
PY
}

@test "I-UPS-CLI-011: helix scrum local decide pivot persists the pivot result" {
  loop_id="$(create_scrum_loop L4 "pivot" "pivot" "PLAN-079")"
  run_scrum_poc "$loop_id" >/dev/null
  run_scrum_verify "$loop_id" >/dev/null
  output="$(run_scrum_decide "$loop_id" pivot)"

  [[ "$output" == *"[scrum] $loop_id -> S3 (pivot)"* ]]

  row_json="$(scrum_row_json "$loop_id")"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["state"] == "S3", row
assert row["decide_result"] == "pivot", row
assert row["parent_loop_id"] is None, row
PY
}
