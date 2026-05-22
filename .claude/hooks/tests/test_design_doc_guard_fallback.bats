#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  HOOK="$REPO_ROOT/.claude/hooks/pretooluse-design-doc-web-search-guard.sh"
  TMP_ROOT="$(mktemp -d)"
  HOME_DIR="$TMP_ROOT/home"
  PROJECT_ROOT="$TMP_ROOT/project"
  TRANSCRIPT_DIR="$TMP_ROOT/transcripts"
  DB_PATH="$TMP_ROOT/helix.db"
  PAYLOAD_FILE="$TMP_ROOT/payload.json"
  mkdir -p "$HOME_DIR/.claude/projects" "$PROJECT_ROOT/docs/plans" "$TRANSCRIPT_DIR"
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
  local transcript_path="${2:-}"
  python3 - "$path" "$transcript_path" <<'PY'
import json
import sys

path, transcript_path = sys.argv[1], sys.argv[2]
payload = {
    "tool_name": "Write",
    "tool_input": {
        "file_path": path,
        "content": "# title\n",
    },
}
if transcript_path:
    payload["transcript_path"] = transcript_path
print(json.dumps(payload, ensure_ascii=False))
PY
}

invoke_hook() {
  local payload="$1"
  shift
  printf '%s' "$payload" >"$PAYLOAD_FILE"
  env \
    HOME="$HOME_DIR" \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$TRANSCRIPT_DIR" \
    HELIX_DESIGN_DOC_GUARD_DB_PATH="$DB_PATH" \
    "$@" \
    bash "$HOOK" <"$PAYLOAD_FILE"
}

write_transcript() {
  local path="$1"
  local with_web="$2"
  mkdir -p "$(dirname "$path")"
  if [[ "$with_web" == "web" ]]; then
    cat >"$path" <<'EOF'
{"sessionId":"sess-demo","tool_name":"WebSearch","tool_input":{"query":"design doc guardrail"}}
EOF
  else
    cat >"$path" <<'EOF'
{"sessionId":"sess-demo","tool_name":"Read","tool_input":{"file_path":"README.md"}}
EOF
  fi
}

project_slug() {
  python3 - "$PROJECT_ROOT" <<'PY'
from pathlib import Path
import sys

project_root = Path(sys.argv[1]).resolve(strict=False).as_posix()
print("-" + project_root.lstrip("/").replace("/", "-"))
PY
}

@test "missing session でも payload transcript_path に WebSearch 履歴があれば pass + warning" {
  transcript="$TRANSCRIPT_DIR/current.jsonl"
  write_transcript "$transcript" web
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-911-pass.md" "$transcript")"
  run invoke_hook "$payload" HELIX_SESSION_ID=
  [ "$status" -eq 0 ]
  [[ "$output" == *"WARN: session_id missing"* ]]
  [[ "$output" == *"transcript_path fallback"* ]]
}

@test "missing session かつ transcript に履歴がなければ block を維持する" {
  transcript="$TRANSCRIPT_DIR/current.jsonl"
  write_transcript "$transcript" none
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-912-block.md" "$transcript")"
  run invoke_hook "$payload" HELIX_SESSION_ID=
  [ "$status" -eq 2 ]
  [[ "$output" == *"session_id=missing"* ]]
}

@test "project latest transcript fallback は直近 1 時間の WebSearch 履歴だけを通す" {
  slug="$(project_slug)"
  transcript="$HOME_DIR/.claude/projects/$slug/11111111-2222-4333-8444-555555555555.jsonl"
  write_transcript "$transcript" web
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-913-latest.md")"
  run invoke_hook "$payload" HELIX_SESSION_ID=
  [ "$status" -eq 0 ]
  [[ "$output" == *"project_latest fallback"* ]]
}

@test "project latest transcript fallback でも stale file は通さない" {
  slug="$(project_slug)"
  transcript="$HOME_DIR/.claude/projects/$slug/22222222-3333-4444-8555-666666666666.jsonl"
  write_transcript "$transcript" web
  python3 - "$transcript" <<'PY'
from pathlib import Path
import os
import sys
import time

path = Path(sys.argv[1])
old = time.time() - (2 * 60 * 60)
os.utime(path, (old, old))
PY
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-914-stale.md")"
  run invoke_hook "$payload" HELIX_SESSION_ID=
  [ "$status" -eq 2 ]
  [[ "$output" == *"session_id=missing"* ]]
}

@test "HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1 は理由付きで warning pass" {
  payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-915-bypass.md")"
  run invoke_hook "$payload" \
    HELIX_SESSION_ID= \
    HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1 \
    HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION_REASON="temporary claude env gap"
  [ "$status" -eq 0 ]
  [[ "$output" == *"WARN: session_id missing but bypassed"* ]]
  [[ "$output" == *"temporary claude env gap"* ]]
}
