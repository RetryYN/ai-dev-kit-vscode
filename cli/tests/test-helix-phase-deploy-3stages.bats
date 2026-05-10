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
G5:
  name: "G5 phase smoke"
  static: []
  ai: []
G6:
  name: "G6 pre-smoke"
  static: []
  ai: []
G6.5:
  name: "G6.5 smoke"
  static:
    - name: "smoke"
      cmd: "echo ok"
      level: advisory
  ai: []
G6.7:
  name: "G6.7 smoke"
  static:
    - name: "smoke"
      cmd: "echo ok"
      level: advisory
  ai: []
G6.9:
  name: "G6.9 smoke"
  static:
    - name: "smoke"
      cmd: "echo ok"
      level: advisory
  ai: []
G7:
  name: "G7 smoke"
  static: []
  ai: []
YAML
}

write_phase_state() {
  local g6_status="${1:-pending}"
  local g65_status="${2:-pending}"
  local g67_status="${3:-pending}"
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<YAML
project: phase-deploy-3stages
current_mode: forward
current_phase: L6
gates:
  G5:
    status: passed
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

@test "phase template has L6.5 / L6.7 / L6.9 defined" {
  run grep -cE "L6\.[579]" "$HELIX_ROOT/cli/templates/phase.yaml"
  [ "$status" -eq 0 ]
  [ "$output" -ge 3 ]
}

@test "phase template keeps L6.5 grep match" {
  run grep "L6\.5" "$HELIX_ROOT/cli/templates/phase.yaml"
  [ "$status" -eq 0 ]
  [[ "$output" == *"L6.5"* ]]
}

@test "phase template keeps L6.7 grep match" {
  run grep "L6\.7" "$HELIX_ROOT/cli/templates/phase.yaml"
  [ "$status" -eq 0 ]
  [[ "$output" == *"L6.7"* ]]
}

@test "phase template keeps L6.9 grep match" {
  run grep "L6\.9" "$HELIX_ROOT/cli/templates/phase.yaml"
  [ "$status" -eq 0 ]
  [[ "$output" == *"L6.9"* ]]
}

@test "helix gate G6.5 dry-run smoke is accepted" {
  write_gate_checks_minimal
  write_phase_state passed pending pending

  run "$HELIX_ROOT/cli/helix" gate G6.5 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G6.5: G6.5 smoke ==="* ]]
  [[ "$output" != *"無効なゲート"* ]]
  [[ "$output" == *"[dry-run][advisory] smoke: echo ok"* ]]
  [[ "$output" == *"次のアクション: helix gate G6.7 に進んでください"* ]]
}

@test "helix gate G6.7 dry-run smoke is accepted" {
  write_gate_checks_minimal
  write_phase_state passed passed pending

  run "$HELIX_ROOT/cli/helix" gate G6.7 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G6.7: G6.7 smoke ==="* ]]
  [[ "$output" != *"無効なゲート"* ]]
  [[ "$output" == *"[dry-run][advisory] smoke: echo ok"* ]]
  [[ "$output" == *"次のアクション: helix gate G6.9 に進んでください"* ]]
}

@test "helix gate G6.9 dry-run smoke is accepted" {
  write_gate_checks_minimal
  write_phase_state passed passed passed

  run "$HELIX_ROOT/cli/helix" gate G6.9 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"=== G6.9: G6.9 smoke ==="* ]]
  [[ "$output" != *"無効なゲート"* ]]
  [[ "$output" == *"[dry-run][advisory] smoke: echo ok"* ]]
  [[ "$output" == *"次のアクション: helix gate G7 に進んでください"* ]]
}
