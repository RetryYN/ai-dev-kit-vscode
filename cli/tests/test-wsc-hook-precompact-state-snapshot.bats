#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-06

json_field() {
  local json_text="$1"
  local field_name="$2"
  JSON_TEXT="$json_text" FIELD_NAME="$field_name" python3 - <<'PY'
import json
import os

lines = [line for line in os.environ["JSON_TEXT"].splitlines() if line.strip()]
value = json.loads(lines[-1])
for segment in os.environ["FIELD_NAME"].split("."):
    value = value[segment]
if isinstance(value, bool):
    print("true" if value else "false")
else:
    print(value)
PY
}

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/precompact-state-snapshot.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT/.helix"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "UT-WSC-06: python3 失敗時は fail-open fallback で continue する" {
  run env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=1 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-fallback" \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="/sys/precompact-blocked-sessions" \
    /bin/bash "$HOOK" <<<'{}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [[ "$(json_field "$output" "message")" == *"fail-open fallback"* ]]
}

@test "UT-WSC-06: persist_failed=false なら backup を残して continue する" {
  local backup_dir="$TMP_ROOT/backups"
  local blocked_file="$TMP_ROOT/blocked-sessions"

  run env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    HELIX_PRECOMPACT_BACKUP_DIR="$backup_dir" \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="$blocked_file" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=0 \
    HELIX_STATE_PERSIST_FAILED=0 \
    HELIX_LAST_STATE_PERSIST_EXIT_CODE=0 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-continue" \
    /bin/bash "$HOOK" <<<'{}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [ "$(json_field "$output" "conditions.persist_failed")" = "false" ]
  run bash -lc "find '$backup_dir' -type f | wc -l | tr -d ' '"
  [ "$status" -eq 0 ]
  [ "$output" -ge 1 ]
}

@test "UT-WSC-06: 3 条件 AND 成立時は block して blocked_sessions_file に session_id を追記する" {
  local blocked_file="$TMP_ROOT/blocked-sessions"

  run env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="$blocked_file" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=1 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-block" \
    /bin/bash "$HOOK" <<<'{}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "block" ]
  [ "$(json_field "$output" "conditions.persist_failed")" = "true" ]
  [ "$(json_field "$output" "conditions.unsaved_decisions")" = "true" ]
  [ "$(json_field "$output" "conditions.one_shot_consumed")" = "false" ]
  grep -qx 'session-block' "$blocked_file"
}

@test "UT-WSC-06: 同じ session の 2 回目は one_shot_consumed=true で continue する" {
  local backup_dir="$TMP_ROOT/backups-second"
  local blocked_file="$TMP_ROOT/blocked-sessions-second"

  run env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="$blocked_file" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=1 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-retry" \
    /bin/bash "$HOOK" <<<'{}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "block" ]

  run env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    HELIX_PRECOMPACT_BACKUP_DIR="$backup_dir" \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="$blocked_file" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=1 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-retry" \
    /bin/bash "$HOOK" <<<'{}'
  [ "$status" -eq 0 ]
  [ "$(json_field "$output" "decision")" = "continue" ]
  [ "$(json_field "$output" "conditions.one_shot_consumed")" = "true" ]
}
