#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cp "$HELIX_ROOT/cli/templates/gate-checks.yaml" "$PROJECT_ROOT/.helix/gate-checks.yaml"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1
}

teardown() {
  rm -rf "$TMP_ROOT"
}

write_phase() {
  local g7_status="${1:-pending}"
  local g9_status="${2:-pending}"
  local g10_status="${3:-pending}"
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<YAML
project: gate-g9-g11-test
current_phase: L9
sprint:
  drive: be
  ui: false
gates:
  G7:
    status: $g7_status
  G9:
    status: $g9_status
  G10:
    status: $g10_status
  G11:
    status: pending
YAML
}

@test "helix gate G9 --dry-run is accepted" {
  write_phase passed pending pending

  run "$HELIX_ROOT/cli/helix" gate G9 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G9: デプロイ検証ゲート ==="* ]]
  [[ "$output" != *"無効なゲート"* ]]
}

@test "helix gate G10 --dry-run is accepted" {
  write_phase passed passed pending

  run "$HELIX_ROOT/cli/helix" gate G10 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G10: 観測完了ゲート ==="* ]]
  [[ "$output" != *"無効なゲート"* ]]
}

@test "helix gate G11 --dry-run is accepted" {
  write_phase passed passed passed

  run "$HELIX_ROOT/cli/helix" gate G11 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G11: 運用学習完了ゲート ==="* ]]
  [[ "$output" != *"無効なゲート"* ]]
}

@test "G9 fails when G7 has not passed" {
  write_phase pending pending pending

  run "$HELIX_ROOT/cli/helix" gate G9 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G7 が未通過です"* ]]
}

@test "G10 fails when G9 has not passed" {
  write_phase passed pending pending

  run "$HELIX_ROOT/cli/helix" gate G10 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G9 が未通過です"* ]]
}

@test "G11 fails when G10 is failed" {
  write_phase passed passed failed

  run "$HELIX_ROOT/cli/helix" gate G11 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G10 が未通過です"* ]]
  [[ "$output" == *"status: failed"* ]]
}
