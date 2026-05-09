#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/docs" "$HOME_DIR"
  printf "mini PLAN fixture\n" > "$PROJECT_ROOT/docs/source.md"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix plan --mini --help shows mini plan options" {
  run "$HELIX_ROOT/cli/helix" plan --mini --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"--mini"* ]]
  [[ "$output" == *"--parent <PLAN-NNN|MPLAN-NNN>"* ]]
  [[ "$output" == *"helix plan --mini --parent PLAN-029"* ]]
}

@test "helix plan --mini creates mini plan file and records db relation" {
  run "$HELIX_ROOT/cli/helix" plan --mini --parent PLAN-001 --title "test mini" --file docs/source.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"作成: .helix/mini-plans/MPLAN-001.yaml"* ]]
  [[ "$output" == *"ID: MPLAN-001"* ]]
  [[ "$output" == *"Parent: PLAN-001"* ]]

  [ -f "$PROJECT_ROOT/.helix/mini-plans/MPLAN-001.yaml" ]
  grep -q '^kind: mini-plan$' "$PROJECT_ROOT/.helix/mini-plans/MPLAN-001.yaml"
  grep -q '^parent_plan_id: PLAN-001$' "$PROJECT_ROOT/.helix/mini-plans/MPLAN-001.yaml"
  grep -q '^  - L1$' "$PROJECT_ROOT/.helix/mini-plans/MPLAN-001.yaml"
  grep -q '^  - L6$' "$PROJECT_ROOT/.helix/mini-plans/MPLAN-001.yaml"

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import json
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
row = conn.execute(
    "SELECT parent_entry_id, ref, metadata FROM entries WHERE id = ?",
    ("mini-plan:MPLAN-001",),
).fetchone()
link = conn.execute(
    "SELECT metadata FROM links WHERE from_id = ? AND to_id = ? AND kind = 'derives_from'",
    ("mini-plan:MPLAN-001", "plan:PLAN-001"),
).fetchone()
conn.close()

assert row is not None
assert row["parent_entry_id"] == "plan:PLAN-001"
assert row["ref"] == ".helix/mini-plans/MPLAN-001.yaml"
payload = json.loads(row["metadata"])
assert payload["parent_plan_id"] == "PLAN-001"
assert payload["child_plan_id"] == "MPLAN-001"
assert link is not None
assert json.loads(link["metadata"]) == {
    "child_plan_id": "MPLAN-001",
    "parent_plan_id": "PLAN-001",
}
PY
  [ "$status" -eq 0 ]
}

@test "helix plan --mini rejects self cycle via explicit plan id" {
  run "$HELIX_ROOT/cli/helix" plan --mini --plan-id MPLAN-777 --parent MPLAN-777 --title "cycle"
  [ "$status" -ne 0 ]
  [[ "$output" == *"循環"* ]]
}
