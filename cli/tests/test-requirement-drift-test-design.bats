#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
}

@test "requirement_drift test design contract stays pinned by pytest" {
  run python3 -m pytest "$HELIX_ROOT/cli/lib/tests/test_requirement_drift_test_design.py" -q
  [ "$status" -eq 0 ]
  [[ "$output" == *"5 passed"* ]]
}
