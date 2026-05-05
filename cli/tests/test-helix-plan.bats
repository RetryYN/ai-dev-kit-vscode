#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/docs" "$HOME_DIR"
  printf "PLAN fixture\n" > "$PROJECT_ROOT/docs/source.md"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "helix plan help lists lifecycle subcommands" {
  run "$HELIX_ROOT/cli/helix" plan --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"draft"* ]]
  [[ "$output" == *"review"* ]]
  [[ "$output" == *"finalize"* ]]
  [[ "$output" == *"reset"* ]]
  [[ "$output" == *"status"* ]]
}

@test "helix plan list reports empty state" {
  run "$HELIX_ROOT/cli/helix" plan list
  [ "$status" -eq 0 ]
  [[ "$output" == *"プランは登録されていません。"* ]]
}

@test "helix plan draft creates first plan yaml with source file" {
  run "$HELIX_ROOT/cli/helix" plan draft --title "Plan CLI Coverage" --file docs/source.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"作成: .helix/plans/PLAN-001.yaml"* ]]
  [[ "$output" == *"ID: PLAN-001"* ]]

  [ -f "$PROJECT_ROOT/.helix/plans/PLAN-001.yaml" ]
  grep -q '^id: PLAN-001$' "$PROJECT_ROOT/.helix/plans/PLAN-001.yaml"
  grep -q '^title: "Plan CLI Coverage"$' "$PROJECT_ROOT/.helix/plans/PLAN-001.yaml"
  grep -q '^status: draft$' "$PROJECT_ROOT/.helix/plans/PLAN-001.yaml"
  grep -q '^source_file: "docs/source.md"$' "$PROJECT_ROOT/.helix/plans/PLAN-001.yaml"
}

@test "helix plan draft increments numeric plan id" {
  mkdir -p "$PROJECT_ROOT/.helix/plans"
  cat > "$PROJECT_ROOT/.helix/plans/PLAN-009.yaml" <<'YAML'
id: PLAN-009
title: Existing Plan
status: draft
created_at: "2026-05-01T00:00:00Z"
source_file: null
finalized_at: null
review:
  status: pending
  reviewed_at: null
  review_file: null
YAML

  run "$HELIX_ROOT/cli/helix" plan draft --title "Next Plan"
  [ "$status" -eq 0 ]
  [[ "$output" == *"ID: PLAN-010"* ]]
  [ -f "$PROJECT_ROOT/.helix/plans/PLAN-010.yaml" ]
}

@test "helix plan status shows core fields" {
  "$HELIX_ROOT/cli/helix" plan draft --title "Status Plan" --file docs/source.md >/dev/null

  run "$HELIX_ROOT/cli/helix" plan status --id PLAN-001
  [ "$status" -eq 0 ]
  [[ "$output" == *"ID:          PLAN-001"* ]]
  [[ "$output" == *"Title:       Status Plan"* ]]
  [[ "$output" == *"Status:      draft"* ]]
  [[ "$output" == *"Source File: docs/source.md"* ]]
  [[ "$output" == *"Review:"* ]]
  [[ "$output" == *"Status:    pending"* ]]
}

@test "helix plan finalize rejects unapproved review" {
  "$HELIX_ROOT/cli/helix" plan draft --title "Finalize Guard" >/dev/null

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-001
  [ "$status" -ne 0 ]
  [[ "$output" == *"TL review が approve ではないため finalize できません"* ]]
}

@test "helix plan rejects invalid plan id" {
  run "$HELIX_ROOT/cli/helix" plan status --id BAD-001
  [ "$status" -ne 0 ]
  [[ "$output" == *"不正な plan id"* ]]
}
