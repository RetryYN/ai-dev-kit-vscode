#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-02

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
  HOOK="$HELIX_ROOT/.claude/hooks/posttooluse-design-doc-web-search-revert.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/docs/plans" "$PROJECT_ROOT/docs/adr"
  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "bats@example.com"
  git config user.name "Bats"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local payload="$1"
  shift
  env CLAUDE_PROJECT_DIR="$PROJECT_ROOT" "$@" /bin/bash "$HOOK" <<<"$payload"
}

payload_for() {
  local rel_path="$1"
  printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$rel_path"
}

write_doc() {
  local path="$1"
  local line_count="$2"
  {
    printf '%s\n' '---'
    printf '%s\n' 'plan_id: PLAN-901'
    printf '%s\n' 'kind: impl'
    printf '%s\n' 'layer: L4'
    printf '%s\n' '---'
    printf '\n# Body\n'
    for i in $(seq 1 "$line_count"); do
      printf 'line %03d\n' "$i"
    done
  } >"$path"
}

@test "UT-WSC-02: WebSearch 証跡ありなら pass し revert しない" {
  local target="$PROJECT_ROOT/docs/adr/ADR-901-test.md"
  local transcript_dir="$TMP_ROOT/transcripts"
  mkdir -p "$transcript_dir"
  write_doc "$target" 20
  printf '%s\n' '{"tool_name":"WebSearch","query":"design doc research"}' >"$transcript_dir/history.jsonl"

  run run_hook "$(payload_for "docs/adr/ADR-901-test.md")" \
    HELIX_SESSION_ID="session-pass" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$transcript_dir"
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "action")" = "pass" ]
  [ "$(json_field "$output" "reason")" = "verification_passed" ]
  grep -q 'line 020' "$target"
}

@test "UT-WSC-02: 証跡なし + frontmatter 100 行以上は backup を残して block する" {
  local target="$PROJECT_ROOT/docs/plans/PLAN-901-revert.md"
  printf '%s\n' '---' 'plan_id: PLAN-901' 'kind: impl' 'layer: L4' '---' '' '# Baseline' >"$target"
  git add "$target"
  git commit -q -m "baseline"
  write_doc "$target" 110

  run run_hook "$(payload_for "docs/plans/PLAN-901-revert.md")" HELIX_SESSION_ID="session-block"
  [ "$status" -eq 2 ]
  [ "$(json_field "$output" "action")" = "block" ]
  [ "$(json_field "$output" "reason")" = "web_search_history_empty" ]
  backup_path="$(json_field "$output" "backup")"
  [ -f "$backup_path" ]
  grep -q '# Baseline' "$target"
  ! grep -q 'line 110' "$target"
}

@test "UT-WSC-02: 証跡なしでも 100 行未満なら warn のみで revert しない" {
  local target="$PROJECT_ROOT/docs/plans/PLAN-902-warn.md"
  write_doc "$target" 10

  run run_hook "$(payload_for "docs/plans/PLAN-902-warn.md")" HELIX_SESSION_ID="session-warn"
  [ "$status" -eq 1 ]
  [ "$(json_field "$output" "action")" = "warn" ]
  [ "$(json_field "$output" "reason")" = "revert_conditions_not_met" ]
  grep -q 'line 010' "$target"
}

@test "UT-WSC-02: bypass reason 未設定は warn-only で止まる" {
  local target="$PROJECT_ROOT/docs/plans/PLAN-903-bypass.md"
  write_doc "$target" 10

  run run_hook "$(payload_for "docs/plans/PLAN-903-bypass.md")" HELIX_ALLOW_DESIGN_DOC_NO_WEB=1
  [ "$status" -eq 1 ]
  [ "$(json_field "$output" "reason")" = "bypass_reason_missing" ]
}

@test "UT-WSC-02: session_id を検出できない場合は warn-only になる" {
  local target="$PROJECT_ROOT/docs/plans/PLAN-904-session.md"
  write_doc "$target" 10

  run run_hook "$(payload_for "docs/plans/PLAN-904-session.md")"
  [ "$status" -eq 1 ]
  [ "$(json_field "$output" "reason")" = "session_id_missing" ]
}
