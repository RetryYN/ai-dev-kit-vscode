#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"

  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "qa@example.com"
  git config user.name "QA"
  printf '# test\n' > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "test_vmodel_list_shows_4_drives" {
  run "$HELIX_ROOT/cli/helix" vmodel list
  [ "$status" -eq 0 ]
  [[ "$output" == *"drives: be, fe, db, fullstack"* ]]
}

@test "test_vmodel_list_with_drive_be_shows_5_layers" {
  run "$HELIX_ROOT/cli/helix" vmodel list --drive be
  [ "$status" -eq 0 ]
  [[ "$output" == *"drive: be"* ]]
  run env VMODEL_OUTPUT="$output" python3 - <<'PY'
import os

lines = dict(
    line.split(": ", 1)
    for line in os.environ["VMODEL_OUTPUT"].splitlines()
    if ": " in line
)
layers = [item.strip() for item in lines["layers"].split(",")]
assert layers == ["planning", "requirement", "architecture", "detailed", "functional"]
PY
  [ "$status" -eq 0 ]
}

@test "test_vmodel_show_be_planning_succeeds" {
  run "$HELIX_ROOT/cli/helix" vmodel show be planning
  [ "$status" -eq 0 ]
  [[ "$output" == *"drive: be"* ]]
  [[ "$output" == *"layer: planning"* ]]
  [[ "$output" == *"design.review_unit: plan"* ]]
  [[ "$output" == *"test.test_level: operational"* ]]
  [[ "$output" == *"pair.vertical_to: requirement"* ]]
}

@test "test_vmodel_show_invalid_drive_fails" {
  run "$HELIX_ROOT/cli/helix" vmodel show invalid planning
  [ "$status" -eq 2 ]
  [[ "$output" == *"unknown drive: invalid"* ]]
}

@test "test_vmodel_validate_default_passes" {
  run "$HELIX_ROOT/cli/helix" vmodel validate
  [ "$status" -eq 0 ]
  [[ "$output" == *"VALIDATION: OK"* ]]
}

@test "test_vmodel_help_prints_usage" {
  run "$HELIX_ROOT/cli/helix" vmodel --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"使い方: helix vmodel <subcommand>"* ]]
  [[ "$output" == *"list [--drive DRIVE] [--json]"* ]]
  [[ "$output" == *"show <drive> <layer> [--json]"* ]]
  [[ "$output" == *"validate [--config PATH] [--json]"* ]]
}

@test "test_vmodel_list_json_outputs_valid_json" {
  run "$HELIX_ROOT/cli/helix" vmodel list --json
  [ "$status" -eq 0 ]
  run env JSON_PAYLOAD="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_PAYLOAD"])
assert payload["drives"] == ["be", "fe", "db", "fullstack"]
assert len(payload["drives"]) == 4
PY
  [ "$status" -eq 0 ]
}

@test "test_vmodel_show_json_outputs_valid_json" {
  run "$HELIX_ROOT/cli/helix" vmodel show be planning --json
  [ "$status" -eq 0 ]
  run env JSON_PAYLOAD="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_PAYLOAD"])
assert payload["drive"] == "be"
assert payload["layer"] == "planning"
assert payload["design"]["review_unit"] == "plan"
assert payload["test"]["test_level"] == "operational"
PY
  [ "$status" -eq 0 ]
}
