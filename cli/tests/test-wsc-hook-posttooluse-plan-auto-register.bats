#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-04

json_field() {
  local json_text="$1"
  local field_name="$2"
  JSON_TEXT="$json_text" FIELD_NAME="$field_name" python3 - <<'PY'
import json
import os

value = json.loads(os.environ["JSON_TEXT"])
for segment in os.environ["FIELD_NAME"].split("."):
    value = value[segment]
print(value)
PY
}

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/posttooluse-plan-auto-register.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/docs/plans"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local payload="$1"
  shift
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$HOOK" <<<"$payload"
}

@test "UT-WSC-04: frontmatter parse_error は WARNING を返して fail-open する" {
  cat >"$PROJECT_ROOT/docs/plans/PLAN-999-parse-error.md" <<'EOF'
---
title: broken plan
---

# Body
EOF

  run run_hook '{"tool_name":"Write","tool_result":{"filePath":"docs/plans/PLAN-999-parse-error.md"}}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "systemMessage")" == *"frontmatter parse 失敗"* ]]
}
