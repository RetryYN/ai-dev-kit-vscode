#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"
  export HELIX_DISABLE_FEEDBACK=1

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_gate_checks_minimal() {
  cat > "$PROJECT_ROOT/.helix/gate-checks.yaml" <<'YAML'
G6:
  name: "G6 release candidate"
  static: []
  ai: []
G6.5:
  name: "G6.5 Pre-Release static"
  static:
    - name: "pre-release static smoke"
      cmd: "echo ok"
      level: advisory
  ai: []
G6.7:
  name: "G6.7 Pre-Release dynamic"
  static:
    - name: "pre-release dynamic smoke"
      cmd: "echo ok"
      level: advisory
  ai: []
G6.9:
  name: "G6.9 Pre-Release readiness"
  static:
    - name: "pre-release readiness smoke"
      cmd: "echo ok"
      level: advisory
  ai: []
YAML
}

write_phase_state() {
  local g6_status="${1:-pending}"
  local g65_status="${2:-pending}"
  local g67_status="${3:-pending}"
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<YAML
project: pre-release-gates
current_mode: forward
current_phase: L6
gates:
  G6:
    status: $g6_status
  G6.5:
    status: $g65_status
  G6.7:
    status: $g67_status
  G6.9:
    status: pending
  G7:
    status: pending
  G9:
    status: pending
  G10:
    status: pending
  G11:
    status: pending
sprint:
  drive: be
  ui: false
YAML
}

@test "helix gate G6.5 fails before G6 has passed" {
  write_gate_checks_minimal
  write_phase_state pending pending pending

  run "$HELIX_ROOT/cli/helix" gate G6.5 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G6 が未通過です"* ]]
}

@test "helix gate G6.5 dry-run smoke identifies pre-release gate" {
  write_gate_checks_minimal
  write_phase_state passed pending pending

  run "$HELIX_ROOT/cli/helix" gate G6.5 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"G6.5"* ]]
  [[ "$output" != *"無効なゲート"* ]]
}

@test "helix gate G6.7 fails before G6.5 has passed" {
  write_gate_checks_minimal
  write_phase_state passed pending pending

  run "$HELIX_ROOT/cli/helix" gate G6.7 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G6.5 が未通過です"* ]]
}

@test "helix gate G6.7 dry-run passes after G6.5" {
  write_gate_checks_minimal
  write_phase_state passed passed pending

  run "$HELIX_ROOT/cli/helix" gate G6.7 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"G6.7"* ]]
  [[ "$output" != *"前提ゲート"* ]]
}

@test "helix gate G6.9 fails before G6.7 has passed" {
  write_gate_checks_minimal
  write_phase_state passed passed pending

  run "$HELIX_ROOT/cli/helix" gate G6.9 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G6.7 が未通過です"* ]]
}

@test "helix gate G6.9 dry-run passes after G6.7" {
  write_gate_checks_minimal
  write_phase_state passed passed passed

  run "$HELIX_ROOT/cli/helix" gate G6.9 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"G6.9"* ]]
  [[ "$output" != *"前提ゲート"* ]]
}
