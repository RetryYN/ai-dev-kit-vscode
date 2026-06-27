#!/usr/bin/env bats
#
# Retired V2 tombstone — requirement_drift 検出は V3 engine (FN-DET-04) へ委譲済み。
# V2 helper の検出実体は cutover で retire 済み。検出正本 = V3 detector (FN-DET-04) +
# その UT (cli/lib/v3/tests/)。本 bats は旧 V2 CLI 挙動 (JSON drift scan: --json /
# --focus L7 / --check-stale) の回帰用だったが、V3 委譲 (delegated_to_v3=true, V2 no-op)
# を反映した tombstone へ更新した。対応 pytest tombstone = cli/lib/tests/test_requirement_drift.py。
# 委譲は HELIX_V3_DELEGATED_CHECKS で reversible (V2 path は削除でなく no-op 化)。

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
}

@test "requirement_drift pytest tombstone passes (V3 委譲済み)" {
  run python3 -m pytest "$HELIX_ROOT/cli/lib/tests/test_requirement_drift.py" -q
  [ "$status" -eq 0 ]
  [[ "$output" == *"1 passed"* ]]
}

@test "helix-doctor check_requirement_drift は V3 engine へ委譲 (V2 no-op)" {
  run "$HELIX_ROOT/cli/helix-doctor" check_requirement_drift --check-stale
  [ "$status" -eq 0 ]
  [[ "$output" == *"delegated_to_v3=true"* ]]
  [[ "$output" == *"V3 engine"* ]]
}
