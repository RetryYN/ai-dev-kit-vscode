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
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix research dry-run supports layer L2 auto mode" {
  run "$HELIX_ROOT/cli/helix" research --layer L2 --auto --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== HELIX Research Dry Run ==="* ]]
  [[ "$output" == *"layer: L2"* ]]
  [[ "$output" == *"D-TECH-STACK 更新対象"* ]]
}

@test "helix research rejects unsupported layer" {
  run "$HELIX_ROOT/cli/helix" research --layer L1 --auto --dry-run
  [ "$status" -ne 0 ]
  [[ "$output" == *"L2 または L3"* ]]
}
