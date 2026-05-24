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
  git config user.email "route-c8@example.com"
  git config user.name "Route C8 Test"
  echo "# route-c8" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name route-c8 >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_route_suggest_json() {
  local signal="$1"
  local drift_type="${2:-}"

  if [[ -n "$drift_type" ]]; then
    run "$HELIX_ROOT/cli/helix" route suggest --signal "$signal" --drift-type "$drift_type" --json
  else
    run "$HELIX_ROOT/cli/helix" route suggest --signal "$signal" --json
  fi

  [ "$status" -eq 0 ]
}

assert_route_payload() {
  local payload="$1"
  local expected_mode="$2"
  local expected_command="$3"
  local expected_args_json="$4"
  local expected_drift_type="$5"
  local expected_requires_human="$6"
  local expected_requires_preflight="$7"

  ROUTE_JSON="$payload" \
  EXPECTED_MODE="$expected_mode" \
  EXPECTED_COMMAND="$expected_command" \
  EXPECTED_ARGS="$expected_args_json" \
  EXPECTED_DRIFT_TYPE="$expected_drift_type" \
  EXPECTED_REQUIRES_HUMAN="$expected_requires_human" \
  EXPECTED_REQUIRES_PREFLIGHT="$expected_requires_preflight" \
  python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["ROUTE_JSON"])
expected_args = json.loads(os.environ["EXPECTED_ARGS"])

assert payload["mode"] == os.environ["EXPECTED_MODE"], payload
assert payload["drift_type"] == os.environ["EXPECTED_DRIFT_TYPE"], payload

recommended = payload["recommended_command"]
assert set(recommended) == {"schema_version", "command", "args", "safety"}, recommended
assert recommended["schema_version"] == "v1", recommended
assert recommended["command"] == os.environ["EXPECTED_COMMAND"], recommended
assert recommended["args"] == expected_args, recommended

safety = recommended["safety"]
assert set(safety) == {
    "auto_apply",
    "requires_human_approval",
    "requires_preflight",
}, safety
assert safety["auto_apply"] is False, safety
assert safety["requires_human_approval"] is (
    os.environ["EXPECTED_REQUIRES_HUMAN"] == "true"
), safety
assert safety["requires_preflight"] is (
    os.environ["EXPECTED_REQUIRES_PREFLIGHT"] == "true"
), safety
PY
}

function shortcut_signal_dependency_outdated_returns_retrofit_plan_draft_json_contract { #@test
  run_route_suggest_json "dependency_outdated"

  assert_route_payload \
    "$output" \
    "Retrofit" \
    "helix plan draft" \
    '{"kind": "retrofit", "drift_type": "dependency_outdated"}' \
    "dependency_outdated" \
    "false" \
    "false"
}

function drift_type_matrix_is_covered_via_route_suggest_json { #@test
  local -a drift_types=(
    "schema"
    "contract"
    "code_smell"
    "structural"
    "dependency_outdated"
    "upgrade"
    "config_drift"
  )
  local -a expected_modes=(
    "Reverse"
    "Reverse"
    "Refactor"
    "Refactor"
    "Retrofit"
    "Retrofit"
    "Retrofit"
  )
  local -a expected_commands=(
    "helix reverse normalization R0"
    "helix reverse normalization R0"
    "helix plan draft"
    "helix plan draft"
    "helix plan draft"
    "helix plan draft"
    "helix plan draft"
  )
  local -a expected_args=(
    '{}'
    '{}'
    '{"kind": "refactor"}'
    '{"kind": "refactor"}'
    '{"kind": "retrofit", "drift_type": "dependency_outdated"}'
    '{"kind": "retrofit", "drift_type": "upgrade"}'
    '{"kind": "retrofit", "drift_type": "config_drift"}'
  )
  local -a expected_requires_human=(
    "false"
    "false"
    "false"
    "false"
    "false"
    "false"
    "true"
  )

  local i
  for i in "${!drift_types[@]}"; do
    run_route_suggest_json "drift" "${drift_types[$i]}"

    assert_route_payload \
      "$output" \
      "${expected_modes[$i]}" \
      "${expected_commands[$i]}" \
      "${expected_args[$i]}" \
      "${drift_types[$i]}" \
      "${expected_requires_human[$i]}" \
      "false"
  done
}

function route_suggest_json_matches_adr042_contract_shape { #@test
  run_route_suggest_json "config_drift"

  ROUTE_JSON="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["ROUTE_JSON"])
recommended = payload["recommended_command"]

assert isinstance(recommended, dict), recommended
assert recommended["command"] == "helix plan draft", recommended
assert recommended["args"]["kind"] == "retrofit", recommended
assert recommended["args"]["drift_type"] == "config_drift", recommended
assert recommended["safety"]["requires_human_approval"] is True, recommended
PY
}
