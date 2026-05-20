#!/usr/bin/env bats

json_field() {
  local json_text="$1"
  local field_name="$2"
  JSON_TEXT="$json_text" FIELD_NAME="$field_name" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_TEXT"])
value = payload
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
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix/handover" "$HOME_DIR"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "Layer 1: PLAN.md Write で systemMessage に job 候補を出す" {
  local payload_file="$TMP_ROOT/posttooluse.json"
  cat >"$payload_file" <<'EOF'
{"tool_name":"Write","tool_input":{"file_path":"docs/plans/PLAN.md"}}
EOF

  run bash -lc "cat '$payload_file' | '$HELIX_ROOT/.claude/hooks/posttooluse-helix-job-enqueue.sh'"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" decision)" == "continue" ]]
  [[ "$(json_field "$output" systemMessage)" == *"PLAN.md"* ]]
  [[ "$(json_field "$output" systemMessage)" == *"helix job 候補"* ]]
  [[ "$(json_field "$output" authorizedBy)" == "none" ]]
}

@test "Layer 2: statusline は context 残量 4 段階を返す" {
  local state_file="$TMP_ROOT/statusline-state.json"

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=100 TRANSCRIPT_TOKENS=40 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "healthy" ]]

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=200 TRANSCRIPT_TOKENS=60 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "caution" ]]

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=300 TRANSCRIPT_TOKENS=75 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "warning" ]]

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=400 TRANSCRIPT_TOKENS=85 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "critical" ]]
}

@test "Layer 2: statusline は hysteresis と debounce を保持する" {
  local state_file="$TMP_ROOT/statusline-state.json"

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=100 TRANSCRIPT_TOKENS=60 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "caution" ]]
  [[ "$(json_field "$output" debounced)" == "false" ]]

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=110 TRANSCRIPT_TOKENS=48 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "caution" ]]
  [[ "$(json_field "$output" debounced)" == "true" ]]

  run env HELIX_STATUSLINE_STATE_FILE="$state_file" HELIX_STATUSLINE_NOW_EPOCH=140 TRANSCRIPT_TOKENS=43 MAX_TOKENS=100 "$HELIX_ROOT/cli/helix-statusline"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" level)" == "healthy" ]]
}

@test "Layer 3: PreCompact は 3 条件が揃うと block する" {
  local blocked_file="$TMP_ROOT/precompact-blocked-sessions"

  run env \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="$blocked_file" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=1 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-a" \
    "$HELIX_ROOT/.claude/hooks/precompact-state-snapshot.sh"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" decision)" == "block" ]]
  [[ "$(json_field "$output" conditions.persist_failed)" == "true" ]]
  grep -q '^session-a$' "$blocked_file"
}

@test "Layer 3: PreCompact は条件不足または one-shot 消費済みなら continue する" {
  local blocked_file="$TMP_ROOT/precompact-blocked-sessions"
  local backup_dir="$TMP_ROOT/precompact-backups"
  printf 'session-b\n' >"$blocked_file"

  run env \
    HELIX_PRECOMPACT_BLOCKED_SESSIONS_FILE="$blocked_file" \
    HELIX_PRECOMPACT_BACKUP_DIR="$backup_dir" \
    HELIX_PRECOMPACT_STATE_PERSIST_FAILED=1 \
    HELIX_UNSAVED_DECISIONS=1 \
    HELIX_SESSION_ID="session-b" \
    HELIX_PRECOMPACT_MANUAL=1 \
    "$HELIX_ROOT/.claude/hooks/precompact-state-snapshot.sh"
  [ "$status" -eq 0 ]
  [[ "$(json_field "$output" decision)" == "continue" ]]
  [[ "$(json_field "$output" conditions.one_shot_consumed)" == "true" ]]
  [[ -d "$backup_dir" ]]
  run bash -lc "find '$backup_dir' -type f | wc -l | tr -d ' '"
  [ "$status" -eq 0 ]
  [[ "$output" -ge 1 ]]
}
