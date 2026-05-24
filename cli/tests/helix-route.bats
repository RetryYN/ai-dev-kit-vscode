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
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "route@example.com"
  git config user.name "Route Test"
  echo "# route" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name route >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix route help prints usage" {
  run "$HELIX_ROOT/cli/helix" route help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage: helix route"* ]]
  [[ "$output" == *"list-signals"* ]]
}

@test "helix route eval returns JSON by default" {
  run "$HELIX_ROOT/cli/helix" route eval --signal drift
  [ "$status" -eq 0 ]

  ROUTE_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["ROUTE_JSON"])
assert payload["signal"] == "drift", payload
assert payload["mode"] == "Reverse", payload
assert payload["kind"] == "reverse", payload
PY
}

@test "helix route eval --format command prints suggest_command only" {
  run "$HELIX_ROOT/cli/helix" route eval --signal drift --format command
  [ "$status" -eq 0 ]
  [ "$output" = "helix plan draft --kind reverse" ]
}

@test "helix route eval accepts detect payload from stdin" {
  run bash -c "printf '%s' '[{\"detector\":\"axis_01_drift\",\"status\":\"drift\",\"result\":{\"uncertainty\":\"low\",\"impact\":\"high\",\"env\":\"dev\"}}]' | \"$HELIX_ROOT/cli/helix\" route eval --from-json /dev/stdin"
  [ "$status" -eq 0 ]

  ROUTE_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["ROUTE_JSON"])
assert isinstance(payload, list), payload
assert payload[0]["priority"] == "P1", payload
assert payload[0]["suggest_command"] == "helix plan draft --kind reverse", payload
PY
}

@test "helix route list-signals shows 7 signals and 1 alias" {
  run "$HELIX_ROOT/cli/helix" route list-signals
  [ "$status" -eq 0 ]
  [[ "$output" == *"drift mode=Reverse"* ]]
  [[ "$output" == *"incident mode=Incident"* ]]
  [[ "$output" == *"degradation mode=alias"* ]]
  [ "$(printf '%s\n' "$output" | wc -l | tr -d ' ')" -eq 8 ]
}

@test "helix commands check stays consistent after route registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
