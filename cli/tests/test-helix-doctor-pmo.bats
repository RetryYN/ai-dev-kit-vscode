#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  HELIX_TEST_TMPDIR="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$HELIX_TEST_TMPDIR"
  export HOME="$HELIX_TEST_TMPDIR/helix-home"
  mkdir -p "$HOME"
}

teardown() {
  rm -rf "$HELIX_TEST_TMPDIR" 2>/dev/null || true
}

@test "helix doctor shows pmo role consistency" {
  run "$HELIX_ROOT/cli/helix-doctor"
  [ "$status" -eq 0 ]
  [[ "$output" == *"✓ pmo role consistency"* ]]
}
