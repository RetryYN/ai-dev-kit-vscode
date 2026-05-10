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
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cp "$HELIX_ROOT/cli/templates/phase.yaml" "$PROJECT_ROOT/.helix/phase.yaml"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix reverse design --help shows design usage" {
  run "$HELIX_ROOT/cli/helix" reverse design --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage:"* ]]
  [[ "$output" == *"--plans <path>"* ]]
  [[ "$output" == *"D0-design-evidence-map.yaml"* ]]
}

@test "helix reverse design defaults to run alias starting R0" {
  run "$HELIX_ROOT/cli/helix" reverse design --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: design R0"* ]]
  [[ "$output" == *"Role:   research"* ]]
  [[ "$output" == *"D0-design-evidence-map.yaml"* ]]
}

@test "helix reverse design run --dry-run starts R0" {
  run "$HELIX_ROOT/cli/helix" reverse design run --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: design R0"* ]]
  [[ "$output" == *"helix codex --role research"* ]]
}

@test "helix reverse design status returns empty status JSON" {
  run "$HELIX_ROOT/cli/helix" reverse design status

  [ "$status" -eq 0 ]
  [[ "$output" == *'"reverse_type": "design"'* ]]
  [[ "$output" == *'"RG0": "pending"'* ]]
  [[ "$output" == *'"RGC": "pending"'* ]]
  [[ "$output" == *'"artifacts": []'* ]]
}

@test "helix reverse design retry R2 --dry-run bypasses prerequisites" {
  run "$HELIX_ROOT/cli/helix" reverse design retry R2 --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: design R2"* ]]
  [[ "$output" == *"Role:   tl"* ]]
  [[ "$output" == *"D2-design-dag.yaml"* ]]
}

@test "helix reverse design --invalidate-forward is parse error" {
  run "$HELIX_ROOT/cli/helix" reverse design --invalidate-forward

  [ "$status" -ne 0 ]
  [[ "$output" == *"--invalidate-forward is valid only for reverse type 'code'"* ]]
}

@test "helix reverse code invalidate-forward covers run gates" {
  run "$HELIX_ROOT/cli/helix" reverse code retry R2 --invalidate-forward --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Forward gates (G2-G11)"* ]]
}

@test "helix reverse upgrade dry-run starts U0 harness" {
  run "$HELIX_ROOT/cli/helix" reverse upgrade --from v1 --to v2 --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: upgrade R0"* ]]
  [[ "$output" == *"Role:   se"* ]]
  [[ "$output" == *"U0-upgrade-context.yaml"* ]]
  [[ "$output" == *"from=v1 to=v2"* ]]
}

@test "helix reverse upgrade rgc is skipped by design" {
  run "$HELIX_ROOT/cli/helix" reverse upgrade rgc

  [ "$status" -ne 0 ]
  [[ "$output" == *"upgrade RGC is skipped"* ]]
}

@test "helix reverse normalization retry R2 dry-run bypasses prerequisites" {
  run "$HELIX_ROOT/cli/helix" reverse normalization retry R2 --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: normalization R2"* ]]
  [[ "$output" == *"N2-normalization-drift.yaml"* ]]
}

@test "helix reverse normalization R1 is skipped" {
  run "$HELIX_ROOT/cli/helix" reverse normalization R1 --dry-run

  [ "$status" -ne 0 ]
  [[ "$output" == *"normalization R1 is skipped"* ]]
}

@test "helix reverse fullback dry-run starts F0 harness" {
  run "$HELIX_ROOT/cli/helix" reverse fullback --artifact .helix/handover --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: fullback R0"* ]]
  [[ "$output" == *"F0-fullback-evidence.yaml"* ]]
  [[ "$output" == *"artifact=.helix/handover"* ]]
}

@test "legacy helix reverse R0 aliases code R0" {
  run "$HELIX_ROOT/cli/helix" reverse R0 --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX: code R0"* ]]
  [[ "$output" == *"Role:   legacy"* ]]
  [[ "$output" == *"R0-evidence-map.yaml"* ]]
}

@test "legacy helix reverse status aliases code status" {
  run "$HELIX_ROOT/cli/helix" reverse status

  [ "$status" -eq 0 ]
  [[ "$output" == *"Reverse HELIX Status"* ]]
  [[ "$output" == *"reverse_type: code"* ]]
  [[ "$output" == *"RG0: pending"* ]]
}
