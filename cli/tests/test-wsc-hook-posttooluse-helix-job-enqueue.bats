#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-03

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
  HOOK="$HELIX_ROOT/.claude/hooks/posttooluse-helix-job-enqueue.sh"
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

@test "UT-WSC-03: explicit consent 時は advisory に承認根拠を載せる" {
  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"docs/plans/PLAN-123-test.md"}}' \
    HELIX_JOB_EXPLICIT_CONSENT=1
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [ "$(json_field "$output" "authorizedBy")" = "explicit_consent" ]
  [[ "$(json_field "$output" "systemMessage")" == *"PLAN-123-test.md"* ]]
}

@test "UT-WSC-03: consent 不要設定なら consent_not_required を返す" {
  run run_hook '{"tool_name":"Write","tool_input":{"file_path":"docs/adr/ADR-123-test.md"}}' \
    HELIX_JOB_CONSENT_REQUIRED=0
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "authorizedBy")" = "consent_not_required" ]
  [[ "$(json_field "$output" "systemMessage")" == *"承認根拠: consent_not_required"* ]]
}

@test "UT-WSC-03: consent_required=true かつ承認根拠なしなら advisory-only で候補提示する" {
  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"docs/plans/PLAN-456-test.md"}}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [ "$(json_field "$output" "authorizedBy")" = "none" ]
  [[ "$(json_field "$output" "systemMessage")" == *"PLAN-456-test.md"* ]]
  [[ "$(json_field "$output" "systemMessage")" == *"advisory のみ"* ]]
  [[ "$(json_field "$output" "systemMessage")" == *"worker pop は禁止"* ]]
}

@test "UT-WSC-03: 対象外ツールは無出力で fail-open 継続する" {
  run run_hook '{"tool_name":"Bash","tool_input":{"command":"echo test"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
