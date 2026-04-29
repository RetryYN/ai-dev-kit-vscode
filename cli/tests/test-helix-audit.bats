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

@test "helix-audit help shows usage" {
  run "$HELIX_ROOT/cli/helix-audit" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage: helix audit"* ]]
}

@test "helix-audit a1 shows usage" {
  run "$HELIX_ROOT/cli/helix-audit" a1
  [ "$status" -eq 0 ]
  [[ "$output" == *"Subcommands:"* ]]
}

@test "helix-audit a1 import nonexistent file exits non-zero" {
  run "$HELIX_ROOT/cli/helix-audit" a1 import --file nonexistent.yaml
  [ "$status" -ne 0 ]
  [[ "$output" == *"file not found"* ]]
}

@test "helix-audit a1 status works on empty DB" {
  run "$HELIX_ROOT/cli/helix-audit" a1 status
  [ "$status" -eq 0 ]
  [[ "$output" == *'"count": 0'* ]]
  [[ "$output" == *'"active": []'* ]]
}

@test "helix-audit a1 import reports lock conflict" {
  run "$HELIX_ROOT/cli/helix" lock acquire --name a1_import --scope project --timeout 0
  [ "$status" -eq 0 ]

  run env HELIX_AUDIT_LOCK_TIMEOUT=0 "$HELIX_ROOT/cli/helix-audit" a1 import --file nonexistent.yaml
  [ "$status" -eq 3 ]
  [[ "$output" == *"lock conflict: a1_import"* ]]
}

@test "helix dispatcher routes audit command" {
  run "$HELIX_ROOT/cli/helix" audit a1 status
  [ "$status" -eq 0 ]
  [[ "$output" == *'"count": 0'* ]]
}
