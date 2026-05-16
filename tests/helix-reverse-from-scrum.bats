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

reverse_row_json() {
  local loop_id="$1"
  python3 - "$DB_PATH" "$loop_id" <<'PY'
import json
import sqlite3
import sys

db_path, loop_id = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM reverse_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
if row is None:
    raise SystemExit(1)
print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
PY
}

create_scrum_loop() {
  local layer="$1"
  local hypothesis="$2"
  local acceptance="$3"

  run "$HELIX_ROOT/cli/helix-scrum" local init \
    --layer "$layer" \
    --hypothesis "$hypothesis" \
    --acceptance "$acceptance"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

run_scrum_poc() {
  local loop_id="$1"
  run "$HELIX_ROOT/cli/helix-scrum" local poc --loop-id "$loop_id"
  [ "$status" -eq 0 ]
}

run_scrum_verify() {
  local loop_id="$1"
  run "$HELIX_ROOT/cli/helix-scrum" local verify --loop-id "$loop_id"
  [ "$status" -eq 0 ]
}

run_scrum_decide() {
  local loop_id="$1"
  local result="$2"
  run "$HELIX_ROOT/cli/helix-scrum" local decide --loop-id "$loop_id" --result "$result"
  [ "$status" -eq 0 ]
}

create_confirmed_scrum_loop() {
  local loop_id
  loop_id="$(create_scrum_loop L4 "reverse seed" "reverse acceptance")"
  run_scrum_poc "$loop_id" >/dev/null
  run_scrum_verify "$loop_id" >/dev/null
  run_scrum_decide "$loop_id" confirmed >/dev/null
  printf '%s' "$loop_id"
}

create_rejected_scrum_loop() {
  local loop_id
  loop_id="$(create_scrum_loop L4 "reverse rejected seed" "reverse acceptance")"
  run_scrum_poc "$loop_id" >/dev/null
  run_scrum_verify "$loop_id" >/dev/null
  run_scrum_decide "$loop_id" rejected >/dev/null
  printf '%s' "$loop_id"
}

create_reverse_loop() {
  local scrum_loop_id="$1"
  run "$HELIX_ROOT/cli/helix-reverse" from-scrum --scrum-loop-id "$scrum_loop_id"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

run_reverse_stage() {
  local loop_id="$1"
  local stage="$2"
  run "$HELIX_ROOT/cli/helix-reverse" local stage --loop-id "$loop_id" --stage "$stage"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

run_reverse_route() {
  local loop_id="$1"
  local target_plan="$2"
  local target_layer="$3"
  run "$HELIX_ROOT/cli/helix-reverse" local route \
    --loop-id "$loop_id" \
    --target-plan "$target_plan" \
    --target-layer "$target_layer"
  [ "$status" -eq 0 ]
  printf '%s' "$output"
}

advance_reverse_to_r4() {
  local scrum_loop_id="$1"
  local reverse_loop_id
  reverse_loop_id="$(create_reverse_loop "$scrum_loop_id")"
  run_reverse_stage "$reverse_loop_id" R1 >/dev/null
  run_reverse_stage "$reverse_loop_id" R2 >/dev/null
  run_reverse_stage "$reverse_loop_id" R3 >/dev/null
  run_reverse_stage "$reverse_loop_id" R4 >/dev/null
  printf '%s' "$reverse_loop_id"
}

@test "I-SRF-CLI-001: helix reverse from-scrum creates a reverse loop" {
  scrum_loop_id="$(create_confirmed_scrum_loop)"
  reverse_loop_id="$(create_reverse_loop "$scrum_loop_id")"

  [[ "$reverse_loop_id" == RL-* ]]

  reverse_json="$(reverse_row_json "$reverse_loop_id")"
  REVERSE_JSON="$reverse_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["REVERSE_JSON"])
assert row["state"] == "R0", row
assert row["parent_scrum_loop_id"].startswith("H-LOCAL-"), row
assert row["reverse_type"] == "scrum-to-forward", row
assert row["target_forward_plan"] is None, row
assert row["target_forward_layer"] is None, row
PY
}

@test "I-SRF-CLI-002: helix reverse from-scrum rejects unconfirmed scrum loops" {
  running_loop_id="$(create_scrum_loop L4 "running" "running")"
  run_scrum_poc "$running_loop_id" >/dev/null
  rejected_loop_id="$(create_rejected_scrum_loop)"

  run "$HELIX_ROOT/cli/helix-reverse" from-scrum --scrum-loop-id "$running_loop_id"
  [ "$status" -ne 0 ]
  [[ "$output" == *"confirmed scrum loop does not exist"* ]]

  run "$HELIX_ROOT/cli/helix-reverse" from-scrum --scrum-loop-id "$rejected_loop_id"
  [ "$status" -ne 0 ]
  [[ "$output" == *"confirmed scrum loop does not exist"* ]]

  [ "$(python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
row = conn.execute("SELECT COUNT(*) FROM reverse_local_loops").fetchone()
print(row[0])
PY
)" -eq 0 ]
}

@test "I-SRF-CLI-003: helix reverse local stage advances to R1" {
  scrum_loop_id="$(create_confirmed_scrum_loop)"
  reverse_loop_id="$(create_reverse_loop "$scrum_loop_id")"

  output="$(run_reverse_stage "$reverse_loop_id" R1)"
  [[ "$output" == *"[reverse] $reverse_loop_id -> R1"* ]]

  reverse_json="$(reverse_row_json "$reverse_loop_id")"
  REVERSE_JSON="$reverse_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["REVERSE_JSON"])
assert row["state"] == "R1", row
PY
}

@test "I-SRF-CLI-004: helix reverse local stage advances through R2 and R3" {
  scrum_loop_id="$(create_confirmed_scrum_loop)"
  reverse_loop_id="$(create_reverse_loop "$scrum_loop_id")"
  run_reverse_stage "$reverse_loop_id" R1 >/dev/null

  output_r2="$(run_reverse_stage "$reverse_loop_id" R2)"
  output_r3="$(run_reverse_stage "$reverse_loop_id" R3)"

  [[ "$output_r2" == *"[reverse] $reverse_loop_id -> R2"* ]]
  [[ "$output_r3" == *"[reverse] $reverse_loop_id -> R3"* ]]

  reverse_json="$(reverse_row_json "$reverse_loop_id")"
  REVERSE_JSON="$reverse_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["REVERSE_JSON"])
assert row["state"] == "R3", row
PY
}

@test "I-SRF-CLI-005: helix reverse local list prints a stable table" {
  active_r0_scrum_id="$(create_confirmed_scrum_loop)"
  active_r0_id="$(create_reverse_loop "$active_r0_scrum_id")"
  active_r1_scrum_id="$(create_confirmed_scrum_loop)"
  active_r1_id="$(create_reverse_loop "$active_r1_scrum_id")"
  run_reverse_stage "$active_r1_id" R1 >/dev/null
  active_r2_scrum_id="$(create_confirmed_scrum_loop)"
  active_r2_id="$(create_reverse_loop "$active_r2_scrum_id")"
  run_reverse_stage "$active_r2_id" R1 >/dev/null
  run_reverse_stage "$active_r2_id" R2 >/dev/null
  routed_scrum_id="$(create_confirmed_scrum_loop)"
  routed_id="$(advance_reverse_to_r4 "$routed_scrum_id")"
  run_reverse_route "$routed_id" PLAN-079 L4 >/dev/null

  run "$HELIX_ROOT/cli/helix-reverse" local list
  [ "$status" -eq 0 ]
  [[ "$output" =~ LOOP_ID[[:space:]]+\|[[:space:]]+SCRUM_LOOP[[:space:]]+\|[[:space:]]+TYPE[[:space:]]+\|[[:space:]]+STATE[[:space:]]+\|[[:space:]]+TARGET_PLAN[[:space:]]+\|[[:space:]]+TARGET_LAYER ]]
  [[ "$output" == *"$active_r0_id"* ]]
  [[ "$output" == *"$active_r1_id"* ]]
  [[ "$output" == *"$active_r2_id"* ]]
  [[ "$output" != *"$routed_id"* ]]
}

@test "I-SRF-CLI-006: helix reverse local route persists target_forward_plan" {
  scrum_loop_id="$(create_confirmed_scrum_loop)"
  reverse_loop_id="$(advance_reverse_to_r4 "$scrum_loop_id")"

  output="$(run_reverse_route "$reverse_loop_id" PLAN-079 L4)"
  [[ "$output" == *"[reverse] $reverse_loop_id routed -> PLAN-079/L4"* ]]

  reverse_json="$(reverse_row_json "$reverse_loop_id")"
  REVERSE_JSON="$reverse_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["REVERSE_JSON"])
assert row["state"] == "R4", row
assert row["target_forward_plan"] == "PLAN-079", row
assert row["target_forward_layer"] == "L4", row
assert row["routed_at"], row
PY
}

@test "I-SRF-CLI-007: helix reverse local route persists target_forward_layer" {
  scrum_loop_id="$(create_confirmed_scrum_loop)"
  reverse_loop_id="$(advance_reverse_to_r4 "$scrum_loop_id")"

  run_reverse_route "$reverse_loop_id" PLAN-079 L3 >/dev/null

  reverse_json="$(reverse_row_json "$reverse_loop_id")"
  REVERSE_JSON="$reverse_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["REVERSE_JSON"])
assert row["state"] == "R4", row
assert row["target_forward_plan"] == "PLAN-079", row
assert row["target_forward_layer"] == "L3", row
PY
}

@test "I-SRF-CLI-008: helix reverse local stats prints routed layer counts" {
  routed_l4_id="$(advance_reverse_to_r4 "$(create_confirmed_scrum_loop)")"
  run_reverse_route "$routed_l4_id" PLAN-079 L4 >/dev/null
  routed_l3_id="$(advance_reverse_to_r4 "$(create_confirmed_scrum_loop)")"
  run_reverse_route "$routed_l3_id" PLAN-079 L3 >/dev/null

  run "$HELIX_ROOT/cli/helix-reverse" local stats
  [ "$status" -eq 0 ]
  [[ "$output" == *"LAYER | COUNT"* ]]
  [[ "$output" =~ L3[[:space:]]+\|[[:space:]]+1 ]]
  [[ "$output" =~ L4[[:space:]]+\|[[:space:]]+1 ]]
  [[ "$output" == *"TOTAL: 2"* ]]
}
