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

  cat > "$PROJECT_ROOT/docs/plans/$doc_name" <<MARKDOWN
---
plan_id: $id
title: Finalize Fixture
status: draft
created: 2026-05-01
finalized: null
---

## Summary

fixture body
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
assert "fixture body" in body, body
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

@test "helix plan finalize updates docs frontmatter and yaml together" {
  write_plan_pair "PLAN-201" '"docs/plans/PLAN-201-sample.md"'

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-201
  [ "$status" -eq 0 ]
  [[ "$output" == *"finalize 完了: PLAN-201"* ]]

  run date -u +"%Y-%m-%d"
  [ "$status" -eq 0 ]
  expected_date="$output"
  assert_finalized_state "PLAN-201" "PLAN-201-sample.md" "$expected_date"
}

@test "helix plan finalize replaces existing draft frontmatter fields" {
  write_plan_pair "PLAN-202" '"docs/plans/PLAN-202-sample.md"'

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-202
  [ "$status" -eq 0 ]

  run grep -n '^status: finalized$' "$PROJECT_ROOT/docs/plans/PLAN-202-sample.md"
  [ "$status" -eq 0 ]
  run grep -n '^finalized: [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}$' "$PROJECT_ROOT/docs/plans/PLAN-202-sample.md"
  [ "$status" -eq 0 ]
}

@test "helix plan finalize rolls back docs when yaml replace fails" {
  write_plan_pair "PLAN-203" '"docs/plans/PLAN-203-sample.md"'

  run env HELIX_PLAN_FRONTMATTER_FAIL_STAGE=plan_replace "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-203
  [ "$status" -ne 0 ]
  [[ "$output" == *"rollback completed"* ]]

  assert_draft_state "PLAN-203" "PLAN-203-sample.md"
}

@test "helix plan finalize keeps both files draft when docs replace fails" {
  write_plan_pair "PLAN-204" '"docs/plans/PLAN-204-sample.md"'

  run env HELIX_PLAN_FRONTMATTER_FAIL_STAGE=docs_replace "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-204
  [ "$status" -ne 0 ]
  [[ "$output" == *"rollback completed"* ]]

  assert_draft_state "PLAN-204" "PLAN-204-sample.md"
}

@test "helix plan finalize resolves docs file by plan id when source_file is null" {
  write_plan_pair "PLAN-205" 'null'

  run "$HELIX_ROOT/cli/helix" plan finalize --id PLAN-205
  [ "$status" -eq 0 ]

  run date -u +"%Y-%m-%d"
  [ "$status" -eq 0 ]
  expected_date="$output"
  assert_finalized_state "PLAN-205" "PLAN-205-sample.md" "$expected_date"
}
