#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  HELIX_TEST_TMPDIR="$(mktemp -d)"
  export HOME="$HELIX_TEST_TMPDIR/helix-home"
  mkdir -p "$HOME"
}

teardown() {
  rm -rf "$HELIX_TEST_TMPDIR"
}

@test "helix doctor shows pmo role consistency" {
  run "$HELIX_ROOT/cli/helix-doctor"
  [ "$status" -eq 0 ]
  [[ "$output" == *"✓ pmo role consistency"* ]]
}
