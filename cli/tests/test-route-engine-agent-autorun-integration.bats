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
  git config user.email "route-agent-autorun@example.com"
  git config user.name "Route Agent AutoRun Test"
  echo "# route-agent-autorun" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name route-agent-autorun >/dev/null
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

  ROUTE_JSON="$payload" \
  EXPECTED_MODE="$expected_mode" \
  EXPECTED_DRIFT_TYPE="$expected_drift_type" \
  EXPECTED_COMMAND="$expected_command" \
  EXPECTED_ARGS="$expected_args_json" \
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
assert recommended["safety"] == {
    "auto_apply": False,
    "requires_human_approval": False,
    "requires_preflight": False,
}, recommended
PY
}

function drive_agent_shortcut_signal_returns_agent_init_contract { #@test
  run_route_suggest_json "ai_agent_construction"

  assert_route_payload \
    "$output" \
    "drive_agent" \
    "ai_agent_construction" \
    "helix agent init" \
    '{"agent_id": "<agent-id>", "summary": "auto-routed from ai_agent_construction", "phase1_drive": "fullstack"}'
}

function drive_agent_alias_signal_returns_agent_init_contract { #@test
  run_route_suggest_json "agent_design_required"

  assert_route_payload \
    "$output" \
    "drive_agent" \
    "ai_agent_construction" \
    "helix agent init" \
    '{"agent_id": "<agent-id>", "summary": "auto-routed from agent_design_required", "phase1_drive": "fullstack"}'
}

function auto_run_shortcut_signal_returns_start_contract { #@test
  run_route_suggest_json "long_running_task"

  assert_route_payload \
    "$output" \
    "auto_run" \
    "long_running_task" \
    "helix auto-run start" \
    '{"plan_id": "<plan-id>", "duration_minutes": 60}'
}

function auto_run_alias_signal_returns_start_contract { #@test
  run_route_suggest_json "context_exhaustion_predicted"

  assert_route_payload \
    "$output" \
    "auto_run" \
    "long_running_task" \
    "helix auto-run start" \
    '{"plan_id": "<plan-id>", "duration_minutes": 60}'
}
