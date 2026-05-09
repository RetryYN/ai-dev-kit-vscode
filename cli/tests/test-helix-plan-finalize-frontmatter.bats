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
  mkdir -p "$PROJECT_ROOT/.helix/plans" "$PROJECT_ROOT/docs/plans" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_plan_pair() {
  local id="$1"
  local source_file="$2"
  local doc_name="${3:-$id-sample.md}"
  local body="${4:-fixture body}"

  cat > "$PROJECT_ROOT/docs/plans/$doc_name" <<MARKDOWN
---
plan_id: $id
title: Finalize Fixture
status: draft
created: 2026-05-01
finalized: null
---

## Summary

$body
MARKDOWN

  cat > "$PROJECT_ROOT/.helix/plans/$id.yaml" <<YAML
id: $id
title: "Finalize Fixture"
status: draft
created_at: "2026-05-01T00:00:00Z"
source_file: $source_file
references: []
artifacts: []
finalized_at: null
review:
  status: approve
  reviewed_at: "2026-05-01T00:00:00Z"
  review_file: ".helix/reviews/plans/$id.json"
YAML
}

write_yaml_only_plan() {
  local id="$1"

  cat > "$PROJECT_ROOT/.helix/plans/$id.yaml" <<YAML
id: $id
title: "Legacy YAML Only"
status: draft
created_at: "2026-05-01T00:00:00Z"
source_file: null
references: []
artifacts: []
finalized_at: null
review:
  status: approve
  reviewed_at: "2026-05-01T00:00:00Z"
  review_file: ".helix/reviews/plans/$id.json"
YAML
}

stage_regression_fixture() {
  local id="$1"
  local source_path

  source_path="$(find "$HELIX_ROOT/docs/plans" -maxdepth 1 -type f -name "$id-*.md" | head -n 1)"
  [ -n "$source_path" ]

  mkdir -p "$PROJECT_ROOT/docs/plans"
  cp "$source_path" "$PROJECT_ROOT/docs/plans/"

  local doc_name
  doc_name="$(basename "$source_path")"
  cat > "$PROJECT_ROOT/.helix/plans/$id.yaml" <<YAML
id: $id
title: "Regression Fixture"
status: draft
created_at: "2026-05-01T00:00:00Z"
source_file: "docs/plans/$doc_name"
references: []
artifacts: []
finalized_at: null
review:
  status: approve
  reviewed_at: "2026-05-01T00:00:00Z"
  review_file: ".helix/reviews/plans/$id.json"
YAML
}

assert_finalized_state() {
  local id="$1"
  local doc_name="${2:-$id-sample.md}"
  local expected_date="$3"

  run python3 - <<PY
from pathlib import Path
import sys

sys.path.insert(0, "$HELIX_ROOT/cli/lib")

import plan_frontmatter
import yaml_parser

plan_path = Path(".helix/plans/$id.yaml")
doc_path = Path("docs/plans/$doc_name")
plan = yaml_parser.parse_yaml(plan_path.read_text(encoding="utf-8"))
frontmatter, body = plan_frontmatter._parse_frontmatter(doc_path.read_text(encoding="utf-8"))

assert plan["status"] == "finalized", plan
assert plan["finalized_at"] == "$expected_date", plan
assert frontmatter["status"] == "finalized", frontmatter
assert frontmatter["finalized"] == "$expected_date", frontmatter
PY
  [ "$status" -eq 0 ]
}

assert_draft_state() {
  local id="$1"
  local doc_name="${2:-$id-sample.md}"

  run python3 - <<PY
from pathlib import Path
import sys

sys.path.insert(0, "$HELIX_ROOT/cli/lib")

import plan_frontmatter
import yaml_parser

plan_path = Path(".helix/plans/$id.yaml")
doc_path = Path("docs/plans/$doc_name")
plan = yaml_parser.parse_yaml(plan_path.read_text(encoding="utf-8"))
frontmatter, _ = plan_frontmatter._parse_frontmatter(doc_path.read_text(encoding="utf-8"))

assert plan["status"] == "draft", plan
assert plan["finalized_at"] is None, plan
assert frontmatter["status"] == "draft", frontmatter
assert frontmatter["finalized"] is None, frontmatter
PY
  [ "$status" -eq 0 ]
}

assert_yaml_only_finalized_state() {
  local id="$1"
  local expected_date="$2"

  run python3 - <<PY
from pathlib import Path
import sys

sys.path.insert(0, "$HELIX_ROOT/cli/lib")

import yaml_parser

plan_path = Path(".helix/plans/$id.yaml")
plan = yaml_parser.parse_yaml(plan_path.read_text(encoding="utf-8"))

assert plan["status"] == "finalized", plan
assert plan["finalized_at"] == "$expected_date", plan
PY
  [ "$status" -eq 0 ]
}

@test "helix plan finalize auto-lint pass keeps finalize success for PLAN-031 through PLAN-038" {
  local plan_id
  for plan_id in PLAN-031 PLAN-032 PLAN-033 PLAN-034 PLAN-035 PLAN-036 PLAN-037 PLAN-038; do
    stage_regression_fixture "$plan_id"
  done

  local plan_ids=(PLAN-031 PLAN-032 PLAN-033 PLAN-034 PLAN-035 PLAN-036 PLAN-037 PLAN-038)
  for plan_id in "${plan_ids[@]}"; do
    run "$HELIX_ROOT/cli/helix" plan finalize --id "$plan_id"
    [ "$status" -eq 0 ]
    [[ "$output" == *"finalize 完了: $plan_id"* ]]
  done

  run date -u +"%Y-%m-%d"
  [ "$status" -eq 0 ]
  expected_date="$output"
  assert_finalized_state "PLAN-031" "$(basename "$(find "$PROJECT_ROOT/docs/plans" -maxdepth 1 -type f -name 'PLAN-031-*.md' | head -n 1)")" "$expected_date"
}

@test "helix plan finalize blocks when auto-lint detects duplicates" {
  write_plan_pair \
    "PLAN-202" \
    '"docs/plans/PLAN-202-sample.md"' \
    "PLAN-202-sample.md" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - DoD:\n    - duplicate を検出したら block する\n\n### §4.3 W-23\n- DoD:\n  - duplicate を検出したら block する'

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-202
  [ "$status" -eq 1 ]
  [[ "$output" == *"duplicate detected のため finalize を中止しました: PLAN-202"* ]]
  [[ "$output" == *"| §2.1 |"* ]]
  assert_draft_state "PLAN-202" "PLAN-202-sample.md"
}

@test "helix plan finalize --no-lint bypasses duplicate block" {
  write_plan_pair \
    "PLAN-203" \
    '"docs/plans/PLAN-203-sample.md"' \
    "PLAN-203-sample.md" \
    $'### §2.1 対象範囲\n- W-23: PLAN lint 拡張\n  - DoD:\n    - duplicate を検出したら block する\n\n### §4.3 W-23\n- DoD:\n  - duplicate を検出したら block する'

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-203 --no-lint
  [ "$status" -eq 0 ]
  [[ "$output" == *"finalize 完了: PLAN-203"* ]]

  run date -u +"%Y-%m-%d"
  [ "$status" -eq 0 ]
  expected_date="$output"
  assert_finalized_state "PLAN-203" "PLAN-203-sample.md" "$expected_date"
}

@test "helix plan finalize skips auto-lint for legacy YAML-only plan" {
  write_yaml_only_plan "PLAN-001"

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-001
  [ "$status" -eq 0 ]
  [[ "$output" == *"auto-lint skipped: legacy YAML-only PLAN (PLAN-001)"* ]]
  [[ "$output" == *"finalize 完了: PLAN-001"* ]]

  run date -u +"%Y-%m-%d"
  [ "$status" -eq 0 ]
  expected_date="$output"
  assert_yaml_only_finalized_state "PLAN-001" "$expected_date"
}

@test "helix plan finalize rolls back docs when yaml replace fails" {
  write_plan_pair "PLAN-204" '"docs/plans/PLAN-204-sample.md"'

  run env HELIX_PLAN_FRONTMATTER_FAIL_STAGE=plan_replace "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-204
  [ "$status" -ne 0 ]
  [[ "$output" == *"rollback completed"* ]]

  assert_draft_state "PLAN-204" "PLAN-204-sample.md"
}

@test "helix plan finalize keeps both files draft when docs replace fails" {
  write_plan_pair "PLAN-205" '"docs/plans/PLAN-205-sample.md"'

  run env HELIX_PLAN_FRONTMATTER_FAIL_STAGE=docs_replace "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-205
  [ "$status" -ne 0 ]
  [[ "$output" == *"rollback completed"* ]]

  assert_draft_state "PLAN-205" "PLAN-205-sample.md"
}

@test "helix plan finalize resolves docs file by plan id when source_file is null" {
  write_plan_pair "PLAN-206" 'null'

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-206
  [ "$status" -eq 0 ]

  run date -u +"%Y-%m-%d"
  [ "$status" -eq 0 ]
  expected_date="$output"
  assert_finalized_state "PLAN-206" "PLAN-206-sample.md" "$expected_date"
}
