#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  HOOK="$REPO_ROOT/.claude/hooks/pretooluse-design-doc-web-search-guard.sh"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  TRANSCRIPT_DIR="$TMP_ROOT/transcripts"
  DB_PATH="$TMP_ROOT/helix.db"
  PAYLOAD_FILE="$TMP_ROOT/payload.json"
  mkdir -p "$PROJECT_ROOT/docs/adr" "$PROJECT_ROOT/docs/plans" "$TRANSCRIPT_DIR"
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
  python3 - "$path" <<'PY'
import json
import sys

path = sys.argv[1]
print(json.dumps({
    "tool_name": "Write",
    "tool_input": {
        "file_path": path,
        "content": "# title\n",
    },
}, ensure_ascii=False))
PY
}

invoke_hook() {
  local payload="$1"
  printf '%s' "$payload" >"$PAYLOAD_FILE"
  env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_SESSION_ID="sess-design-doc-guard" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$TRANSCRIPT_DIR" \
    HELIX_DESIGN_DOC_GUARD_DB_PATH="$DB_PATH" \
    bash "$HOOK" <"$PAYLOAD_FILE"
}

@test "PLAN paths are excluded from design doc guard" {
  local rel
  for rel in \
    "docs/plans/L7/x-plan.md" \
    "docs/plans/process/process-x.md" \
    "docs/plans/discovery/poc-x-plan.md" \
    "docs/plans/PLAN-001.md"
  do
    payload="$(payload_for_write "$PROJECT_ROOT/$rel")"
    run invoke_hook "$payload"
    [ "$status" -eq 0 ]
  done
}

@test "ADR path remains target and blocks without research evidence" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/adr/ADR-001.md")"
  run invoke_hook "$payload"
  [ "$status" -eq 2 ]
}
