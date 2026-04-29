#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_LOCK_OWNER_PID="$$"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "helix lock acquire/release roundtrip" {
  run "$HELIX_ROOT/cli/helix" lock acquire --name bats-basic
  [ "$status" -eq 0 ]
  [[ "$output" == *"acquired name=bats-basic"* ]]
  [ -f "$PROJECT_ROOT/.helix/locks/bats-basic.lock" ]

  run "$HELIX_ROOT/cli/helix" lock release --name bats-basic
  [ "$status" -eq 0 ]
  [[ "$output" == *"released name=bats-basic"* ]]
  [ ! -f "$PROJECT_ROOT/.helix/locks/bats-basic.lock" ]
}

@test "helix lock reports conflict for held lock" {
  run "$HELIX_ROOT/cli/helix" lock acquire --name bats-conflict
  [ "$status" -eq 0 ]
  run "$HELIX_ROOT/cli/helix" lock acquire --name bats-conflict --timeout 0
  [ "$status" -eq 1 ]
  [[ "$output" == *"lock not acquired"* ]]
}
