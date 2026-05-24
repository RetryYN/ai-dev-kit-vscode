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
  git config user.email "route-4mode@example.com"
  git config user.name "Route 4mode Test"
  echo "# route-4mode" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name route-4mode >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_route_suggest_json() {
  local signal="$1"
  run "$HELIX_ROOT/cli/helix" route suggest --signal "$signal" --json
  [ "$status" -eq 0 ]
}

assert_route_payload() {
  local payload="$1"
  local expected_mode="$2"
  local expected_drift_type="$3"
  local expected_command="$4"
  local expected_args_json="$5"
  local expected_requires_human="$6"

  ROUTE_JSON="$payload" \
  EXPECTED_MODE="$expected_mode" \
  EXPECTED_DRIFT_TYPE="$expected_drift_type" \
  EXPECTED_COMMAND="$expected_command" \
  EXPECTED_ARGS="$expected_args_json" \
  EXPECTED_REQUIRES_HUMAN="$expected_requires_human" \
  python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["ROUTE_JSON"])
expected_args = json.loads(os.environ["EXPECTED_ARGS"])

assert payload["mode"] == os.environ["EXPECTED_MODE"], payload
assert payload["drift_type"] == os.environ["EXPECTED_DRIFT_TYPE"], payload

recommended = payload["recommended_command"]
assert recommended["schema_version"] == "v1", recommended
assert recommended["command"] == os.environ["EXPECTED_COMMAND"], recommended
assert recommended["args"] == expected_args, recommended

safety = recommended["safety"]
assert safety == {
    "auto_apply": False,
    "requires_human_approval": os.environ["EXPECTED_REQUIRES_HUMAN"] == "true",
    "requires_preflight": False,
}, safety
PY
}

function scrum_agile_shortcut_signal_returns_init_contract { #@test
  run_route_suggest_json "user_feedback_iteration"

  assert_route_payload \
    "$output" \
    "scrum_agile" \
    "user_feedback_iteration" \
    "helix scrum-agile init" \
    '{}' \
    "false"
}

function incident_shortcut_signal_returns_detect_contract { #@test
  run_route_suggest_json "production_incident"

  assert_route_payload \
    "$output" \
    "incident" \
    "production_incident" \
    "helix incident detect" \
    '{"incident_id": "<incident-id>", "summary": "auto-routed from production_incident", "severity": "P1", "env": "prod"}' \
    "true"
}

function add_feature_shortcut_signal_returns_add_design_contract { #@test
  run_route_suggest_json "feature_addition"

  assert_route_payload \
    "$output" \
    "add_feature" \
    "feature_addition" \
    "helix add-feature add-design" \
    '{"feature": "<feature-id>", "summary": "auto-routed from feature_addition", "requires_plan": "<plan-id>"}' \
    "false"
}

function recovery_shortcut_signal_returns_start_contract { #@test
  run_route_suggest_json "agent_runaway"

  assert_route_payload \
    "$output" \
    "recovery" \
    "agent_runaway" \
    "helix recovery start" \
    '{"plan_id": "<plan-id>", "reopen_point": "HEAD"}' \
    "true"
}
