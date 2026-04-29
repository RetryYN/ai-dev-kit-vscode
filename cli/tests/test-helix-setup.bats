#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "helix setup list shows sample components" {
  run "$HELIX_ROOT/cli/helix" setup list
  [ "$status" -eq 0 ]
  [[ "$output" == *"gitleaks"* ]]
  [[ "$output" == *"gitignore-helix"* ]]
  [[ "$output" == *"redaction-denylist"* ]]
}

@test "helix setup install redaction-denylist creates template" {
  run "$HELIX_ROOT/cli/helix" setup install --name redaction-denylist
  [ "$status" -eq 0 ]
  [[ "$output" == *"created redaction denylist example"* ]]
  [ -f "$PROJECT_ROOT/.helix/audit/redaction-denylist.example.yaml" ]

  run "$HELIX_ROOT/cli/helix" setup install --name redaction-denylist
  [ "$status" -eq 0 ]
  [[ "$output" == *"already exists"* ]]
}

@test "helix setup verify unknown component returns 2" {
  run "$HELIX_ROOT/cli/helix" setup verify --name missing-component
  [ "$status" -eq 2 ]
  [[ "$output" == *"unknown component: missing-component"* ]]
}
