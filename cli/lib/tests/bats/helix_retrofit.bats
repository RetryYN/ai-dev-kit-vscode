#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../../../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$HELIX_ROOT/cli/tests/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "retrofit@example.com"
  git config user.name "Retrofit Test"
  printf "# retrofit\n" > README.md
  git add README.md
  git commit -q -m "init"
  "$HELIX_ROOT/cli/helix" init --project-name retrofit >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix retrofit help and top-level help include retrofit" {
  run "$HELIX_ROOT/cli/helix-retrofit" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"helix retrofit <subcommand>"* ]]
  [[ "$output" == *"init"* ]]
  [[ "$output" == *"matrix"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"retrofit"* ]]
}

@test "helix retrofit init creates matrix config and plan" {
  run "$HELIX_ROOT/cli/helix" retrofit init --slug smoke-test
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/docs/plans/smoke-test-retrofit-matrix.md" ]
  [ -f "$PROJECT_ROOT/cli/config/smoke-test-retrofit.yaml" ]
  [ -f "$PROJECT_ROOT/docs/plans/L7/L7-smoke-test-retrofitplan.md" ]
}

@test "helix retrofit matrix list and update reflect row status" {
  "$HELIX_ROOT/cli/helix" retrofit init --slug matrix-demo >/dev/null

  run "$HELIX_ROOT/cli/helix" retrofit matrix list --slug matrix-demo
  [ "$status" -eq 0 ]
  [[ "$output" == *"| R001 |"* ]]
  [[ "$output" == *"| todo |"* ]]

  run "$HELIX_ROOT/cli/helix" retrofit matrix update --slug matrix-demo --row R001 --status done
  [ "$status" -eq 0 ]
  [[ "$output" == *"\"status\": \"done\""* ]]

  run "$HELIX_ROOT/cli/helix" retrofit matrix show --slug matrix-demo --summary
  [ "$status" -eq 0 ]
  [[ "$output" == *"completion=100%"* ]]
}

@test "helix retrofit status --json exposes completion and warnings" {
  "$HELIX_ROOT/cli/helix" retrofit init --slug status-demo >/dev/null

  run "$HELIX_ROOT/cli/helix" retrofit status --slug status-demo --json
  [ "$status" -eq 0 ]

  ROUTE_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["ROUTE_JSON"])
assert payload["active"] is True, payload
assert payload["summary"]["completion_pct"] == 0, payload
assert payload["summary"]["next_row"] == "R001", payload
PY
}

@test "helix retrofit done marks row done when no blocked rows exist" {
  "$HELIX_ROOT/cli/helix" retrofit init --slug done-demo >/dev/null

  run "$HELIX_ROOT/cli/helix" retrofit done --slug done-demo --row R001
  [ "$status" -eq 0 ]
  [[ "$output" == *"\"completion_pct\": 100"* ]]
}

@test "helix retrofit done returns exit 2 when blocked rows exist" {
  "$HELIX_ROOT/cli/helix" retrofit init --slug blocked-demo >/dev/null
  "$HELIX_ROOT/cli/helix" retrofit matrix add --slug blocked-demo --from old --to new --scope cli --phase L7 >/dev/null
  "$HELIX_ROOT/cli/helix" retrofit matrix update --slug blocked-demo --row R002 --status blocked >/dev/null

  run "$HELIX_ROOT/cli/helix" retrofit done --slug blocked-demo --row R001
  [ "$status" -eq 2 ]
  [[ "$output" == *"blocked rows exist"* ]]
}

@test "helix commands check passes after retrofit registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
