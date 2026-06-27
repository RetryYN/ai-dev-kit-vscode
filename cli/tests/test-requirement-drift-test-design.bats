#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
}

# requirement_drift_test_design 検出は V3 engine (FN-DET-04) へ委譲済み。V2 pytest は
# tombstone 化 (1 passed)。検出正本 = V3 detector + その UT (cli/lib/v3/tests/)。
@test "requirement_drift test design pytest tombstone passes (V3 委譲済み)" {
  run python3 -m pytest "$HELIX_ROOT/cli/lib/tests/test_requirement_drift_test_design.py" -q
  [ "$status" -eq 0 ]
  [[ "$output" == *"1 passed"* ]]
}
