#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  HOOK="$REPO_ROOT/.claude/hooks/pretooluse-design-doc-web-search-guard.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  TRANSCRIPT_DIR="$TMP_ROOT/transcripts"
  DB_PATH="$TMP_ROOT/helix.db"
  PAYLOAD_FILE="$TMP_ROOT/payload.json"
  mkdir -p "$PROJECT_ROOT/docs/plans" "$TRANSCRIPT_DIR"
  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.execute(
    """
    CREATE TABLE agent_slots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      subagent_type TEXT
    )
    """
)
conn.commit()
conn.close()
PY
}

teardown() {
  rm -rf "$TMP_ROOT"
}

payload_for_write() {
  local path="$1"
  local session_id="${2:-}"
  python3 - "$path" "$session_id" <<'PY'
import json
import sys

path, session_id = sys.argv[1], sys.argv[2]
payload = {
    "tool_name": "Write",
    "tool_input": {
        "file_path": path,
        "content": "# title\n",
    },
}
if session_id:
    payload["session_id"] = session_id
print(json.dumps(payload, ensure_ascii=False))
PY
}

invoke_hook() {
  local payload="$1"
  shift
  printf '%s' "$payload" >"$PAYLOAD_FILE"
  env \
    HOME="$TMP_ROOT/home" \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$TRANSCRIPT_DIR" \
    HELIX_DESIGN_DOC_GUARD_DB_PATH="$DB_PATH" \
    "$@" \
    bash "$HOOK" <"$PAYLOAD_FILE"
}

assert_session_id() {
  local expected="$1"
  [[ "$output" == *"session_id=$expected"* ]]
}

@test "Priority 1: HELIX_SESSION_ID を最優先で使う" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-901-env.md" "sess-payload-ignored")"
  run invoke_hook "$payload" HELIX_SESSION_ID=sess-env-001
  [ "$status" -eq 2 ]
  assert_session_id "sess-env-001"
}

@test "Priority 2: payload.session_id を使う" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-902-payload.md" "sess-payload-002")"
  run invoke_hook "$payload" HELIX_SESSION_ID=
  [ "$status" -eq 2 ]
  assert_session_id "sess-payload-002"
}

@test "Priority 3: CLAUDE_TASK_OUTPUT_DIR から UUID を抽出する" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-903-task-output.md")"
  run invoke_hook "$payload" \
    HELIX_SESSION_ID= \
    CLAUDE_TASK_OUTPUT_DIR=/tmp/claude-123/demo/12345678-abcd-4abc-9def-1234567890ab
  [ "$status" -eq 2 ]
  assert_session_id "12345678"
}

@test "Priority 4: CLAUDE_TRANSCRIPT_PATH から UUID を抽出する" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-904-transcript-env.md")"
  run invoke_hook "$payload" \
    HELIX_SESSION_ID= \
    CLAUDE_TRANSCRIPT_PATH=/tmp/transcripts/12345678-abcd-4abc-9def-1234567890ab.jsonl
  [ "$status" -eq 2 ]
  assert_session_id "12345678-abcd-4abc-9def-1234567890ab"
}

@test "Priority 5: 何もなければ missing のまま block を維持する" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-905-missing.md")"
  run invoke_hook "$payload" HELIX_SESSION_ID=
  [ "$status" -eq 2 ]
  assert_session_id "missing"
}
