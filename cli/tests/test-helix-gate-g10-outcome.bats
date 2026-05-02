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
  local g10_status="${1:-pending}"
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<YAML
project: gate-g10-outcome-test
current_phase: L10
sprint:
  drive: be
  ui: false
gates:
  G7:
    status: passed
  G9:
    status: passed
  G10:
    status: $g10_status
    outcome: null
    outcome_owner: null
    outcome_eta: null
    outcome_reason: null
  G11:
    status: pending
YAML
}

phase_value() {
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/phase.yaml" "$1"
}

@test "G10 outcome pass persists passed status and outcome" {
  write_phase pending

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome pass --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [ "$(phase_value gates.G10.status)" = "passed" ]
  [ "$(phase_value gates.G10.outcome)" = "pass" ]
}

@test "G10 outcome watch-continue persists pending status and metadata" {
  write_phase pending

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome watch-continue --outcome-owner TL --outcome-eta 2026-06-01 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [ "$(phase_value gates.G10.status)" = "pending" ]
  [ "$(phase_value gates.G10.outcome)" = "watch-continue" ]
  [ "$(phase_value gates.G10.outcome_owner)" = "TL" ]
  [ "$(phase_value gates.G10.outcome_eta)" = "2026-06-01" ]
}

@test "G10 outcome blocked persists failed status and metadata" {
  write_phase pending

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome blocked --outcome-owner PM --outcome-eta 2026-05-15 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [ "$(phase_value gates.G10.status)" = "failed" ]
  [ "$(phase_value gates.G10.outcome)" = "blocked" ]
  [ "$(phase_value gates.G10.outcome_owner)" = "PM" ]
  [ "$(phase_value gates.G10.outcome_eta)" = "2026-05-15" ]
}

@test "G10 blocked fills default ETA when omitted" {
  write_phase pending
  expected_eta="$(python3 - <<'PY'
import datetime as dt
print((dt.date.today() + dt.timedelta(days=14)).isoformat())
PY
)"

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome blocked --outcome-owner PM --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [ "$(phase_value gates.G10.outcome_eta)" = "$expected_eta" ]
}

@test "G10 outcome failed persists failed status and reason" {
  write_phase pending

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome failed --outcome-reason "incident #42" --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [ "$(phase_value gates.G10.status)" = "failed" ]
  [ "$(phase_value gates.G10.outcome)" = "failed" ]
  [ "$(phase_value gates.G10.outcome_reason)" = "incident #42" ]
}

@test "G10 watch-continue without owner is parse error" {
  write_phase pending

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome watch-continue --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"--outcome-owner が必要です"* ]]
}

@test "outcome flags are G10-only" {
  write_phase passed

  run "$HELIX_ROOT/cli/helix" gate G11 --outcome pass --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"G10 専用"* ]]
}

@test "G10 pass allows G11 prereq but watch-continue blocks it" {
  write_phase pending

  run "$HELIX_ROOT/cli/helix" gate G10 --outcome pass --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  run "$HELIX_ROOT/cli/helix" gate G11 --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]

  write_phase pending
  run "$HELIX_ROOT/cli/helix" gate G10 --outcome watch-continue --outcome-owner TL --outcome-eta 2026-06-01 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  run "$HELIX_ROOT/cli/helix" gate G11 --dry-run --readiness-mode skip
  [ "$status" -ne 0 ]
  [[ "$output" == *"前提ゲート G10 が未通過です"* ]]
  [[ "$output" == *"status: pending"* ]]
}
