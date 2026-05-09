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
  git config user.email "t@t"
  git config user.name "T"
  echo "# test" > README.md
  git add . && git commit -q -m "init"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name interrupt-history >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix interrupt history aggregates local records" {
  "$HELIX_ROOT/cli/helix" interrupt start --reason "API contract changed" --kind constraint --scope auth >/dev/null
  "$HELIX_ROOT/cli/helix" interrupt start --reason "new field requested" --kind new_requirement --scope auth >/dev/null

  run "$HELIX_ROOT/cli/helix" interrupt history

  [ "$status" -eq 0 ]
  [[ "$output" == *"HELIX Interrupt History"* ]]
  [[ "$output" == *"total: 2"* ]]
  [[ "$output" == *"constraint=1"* ]]
  [[ "$output" == *"new_requirement=1"* ]]
}

@test "helix interrupt history --json emits parseable summary" {
  "$HELIX_ROOT/cli/helix" interrupt start --reason "design missing" --kind design_gap >/dev/null

  run "$HELIX_ROOT/cli/helix" interrupt history --json

  [ "$status" -eq 0 ]
  HISTORY_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["HISTORY_JSON"])
assert payload["total"] == 1, payload
assert payload["by_kind"]["design_gap"] == 1, payload
assert payload["recent"][0]["id"] == "INT-001", payload
PY
}
