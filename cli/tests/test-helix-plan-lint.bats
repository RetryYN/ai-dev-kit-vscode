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
  local extra_frontmatter="${5:-}"
  cat > "$file" <<EOF
---
plan_id: $plan_id
title: Test Plan
status: $status
created: 2026-05-09
$extra_frontmatter
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

@test "helix plan lint scopes PLAN-036 self-reference skip to W sections only" {
  run "$HELIX_ROOT/cli/helix" plan lint "$HELIX_ROOT/docs/plans/PLAN-036-codex-post-validation-and-bats-cleanup.md"
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: no contradictory status assertions"* ]]
  [[ "$output" != *"lint skipped for PLAN-036"* ]]
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

@test "helix plan lint warns on exact duplicate DoD bullets" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-044-duplicate-exact.md" \
    "PLAN-044" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - DoD:\n    - 既存の status lint を壊さない\n\n### §4.4 W-23\n- DoD:\n  - 既存の status lint を壊さない'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-044-duplicate-exact.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"WARN: W-23 'DoD' duplicated with §4.4 (similarity=1.00)"* ]]
}

@test "helix plan lint warns on near duplicate Test Plan bullets" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-045-duplicate-near.md" \
    "PLAN-045" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - Test Plan:\n    - 既存 status lint の回帰を防ぐ\n\n### §4.4 W-23\n- Test Plan:\n  - 既存の status lint を壊さず回帰を防ぐ'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-045-duplicate-near.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"WARN: W-23 'Test Plan' duplicated with §4.4 (similarity=0."* ]]
  [[ "$output" != *"similarity=1.00"* ]]
}

@test "helix plan lint ignores unrelated bullets for duplicate detection" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-046-duplicate-none.md" \
    "PLAN-046" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - 影響範囲:\n    - status lint の回帰を防ぐ\n\n### §4.4 W-23\n- 影響範囲:\n  - bats の inventory を更新する'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-046-duplicate-none.md
  [ "$status" -eq 0 ]
  [[ "$output" != *"WARN: W-23"* ]]
}

@test "helix plan lint --duplicates prints markdown report for duplicate rows" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-050-duplicate-report.md" \
    "PLAN-050" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - DoD:\n    - 既存の status lint を壊さない\n\n### §4.4 W-23\n- DoD:\n  - 既存の status lint を壊さない'

  run "$HELIX_ROOT/cli/helix" plan lint --duplicates docs/plans/PLAN-050-duplicate-report.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"| section_a | line_a | section_b | line_b | jaccard | level |"* ]]
  [[ "$output" == *"| §2.1 | 12 | §4.4 W-23 | 16 | 1.00 | highlight |"* ]]
}

@test "helix plan lint --duplicates ignores contradictory status assertions and keeps exit 0" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-051-duplicates-only.md" \
    "PLAN-051" \
    "draft" \
    $'## 実施状況\n現在の status は completed です'

  run "$HELIX_ROOT/cli/helix" plan lint --duplicates docs/plans/PLAN-051-duplicates-only.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"| section_a | line_a | section_b | line_b | jaccard | level |"* ]]
  [[ "$output" != *"frontmatter.status=draft but body asserts completed"* ]]
}

@test "helix plan lint --duplicates observes retroactive plans too" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-035-duplicate-report.md" \
    "PLAN-035" \
    "draft" \
    $'### §2.1 対象範囲\n- W-4: duplicate 観測\n  - Test Plan:\n    - PLAN lint の duplicate-only 出力を確認する\n\n### §4.4 W-4\n- Test Plan:\n  - PLAN lint の duplicate-only 出力を確認する'

  run "$HELIX_ROOT/cli/helix" plan lint --duplicates docs/plans/PLAN-035-duplicate-report.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"| §2.1 | 12 | §4.4 W-4 | 16 | 1.00 | highlight |"* ]]
  [[ "$output" != *"retroactive 対象外"* ]]
}

@test "helix plan lint --duplicates keeps W-section allowlist scoped to status lint only" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-052-allowlist-duplicates.md" \
    "PLAN-052" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - 実装方針:\n    - 既存の status lint を壊さない\n\n### §4.4 W-23\n- 実装方針:\n  - 既存の status lint を壊さない\n  - 現在の status は completed です' \
    "lint_self_reference: true"

  run "$HELIX_ROOT/cli/helix" plan lint --duplicates docs/plans/PLAN-052-allowlist-duplicates.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"| §2.1 | 12 | §4.4 W-23 | 16 | 1.00 | highlight |"* ]]
  [[ "$output" != *"frontmatter.status=draft but body asserts completed"* ]]
}

@test "helix plan lint skips assertive status checks under self-reference W sections" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-047-self-reference-w.md" \
    "PLAN-047" \
    "draft" \
    $'### §4.4 W-23\n- 実装方針:\n  - 現在の status は completed です' \
    "lint_self_reference: true"

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-047-self-reference-w.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: no contradictory status assertions"* ]]
}

@test "helix plan lint still checks self-reference scope outside W sections" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-048-self-reference-scope.md" \
    "PLAN-048" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - 実装方針:\n    - 現在の status は completed です' \
    "lint_self_reference: true"

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-048-self-reference-scope.md
  [ "$status" -eq 1 ]
  [[ "$output" == *"frontmatter.status=draft but body asserts completed"* ]]
}

@test "helix plan lint keeps general plans fully checked" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-049-general-plan.md" \
    "PLAN-049" \
    "draft" \
    $'### §4.4 W-23\n- 実装方針:\n  - 現在の status は completed です'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-049-general-plan.md
  [ "$status" -eq 1 ]
  [[ "$output" == *"frontmatter.status=draft but body asserts completed"* ]]
}

@test "helix plan lint narrows PLAN-036 fallback skip to W sections only" {
  write_plan_md \
    "$PROJECT_ROOT/docs/plans/PLAN-036-self-reference-fallback.md" \
    "PLAN-036" \
    "draft" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - 実装方針:\n    - 現在の status は completed です\n\n### §4.4 W-23\n- 実装方針:\n  - 現在の status は finalized です'

  run "$HELIX_ROOT/cli/helix" plan lint docs/plans/PLAN-036-self-reference-fallback.md
  [ "$status" -eq 1 ]
  [[ "$output" == *"docs/plans/PLAN-036-self-reference-fallback.md:12: frontmatter.status=draft but body asserts completed"* ]]
  [[ "$output" != *"body asserts finalized"* ]]
}
