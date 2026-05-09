#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/docs/plans" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_plan_md() {
  local file="$1"
  local plan_id="$2"
  local status="$3"
  local body="$4"
  cat > "$file" <<EOF
---
plan_id: $plan_id
title: Test Plan
status: $status
created: 2026-05-09
---

$body
EOF
}

@test "helix plan lint allows design explanation under PLAN-036+" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-040-design.md" \
    "PLAN-040" \
    "draft" \
    $'## §4 設計説明\nこの PLAN は draft -> finalized -> completed の 3 段階で運用する。'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-040-design.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: no contradictory status assertions"* ]]
}

@test "helix plan lint allows dated status log entries" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-041-history.md" \
    "PLAN-041" \
    "completed" \
    $'## 更新履歴\n2026-05-09 status finalized'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-041-history.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: no contradictory status assertions"* ]]
}

@test "helix plan lint fails contradictory current status assertion" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-042-invalid.md" \
    "PLAN-042" \
    "draft" \
    $'## 実施状況\n現在の status は completed です'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-042-invalid.md
  [ "$status" -eq 1 ]
  [[ "$output" == *"frontmatter.status=draft but body asserts completed"* ]]
  [[ "$output" == *"現在の status は completed です"* ]]
}

@test "helix plan lint skips PLAN-036 self-reference" {
  run "$HELIX_ROOT/cli/helix" plan lint "$HELIX_ROOT/docs/plans/PLAN-036-codex-post-validation-and-bats-cleanup.md"
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: lint skipped for PLAN-036"* ]]
}

@test "helix plan lint skips retroactive PLAN-035" {
  run "$HELIX_ROOT/cli/helix" plan lint "$HELIX_ROOT/docs/plans/PLAN-035-helix-review-and-bats-cleanup.md"
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: lint skipped for PLAN-035"* ]]
}

@test "helix plan lint still catches assertive mismatch with 本 PLAN phrasing" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-043-assertive.md" \
    "PLAN-043" \
    "finalized" \
    $'## 引用風だが断定\n本 PLAN の status は completed として運用中'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-043-assertive.md
  [ "$status" -eq 1 ]
  [[ "$output" == *"frontmatter.status=finalized but body asserts completed"* ]]
  [[ "$output" == *"本 PLAN の status は completed として運用中"* ]]
}
