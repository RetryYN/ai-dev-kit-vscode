#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md
# UT-WSC-07 / UT-WSC-08 / UT-WSC-10 / UT-WSC-11

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  DB_PATH="$TMP_ROOT/helix.db"
  export HELIX_DB_PATH="$DB_PATH"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  python3 - "$HELIX_ROOT" "$DB_PATH" <<'PY'
import sqlite3
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db

conn = sqlite3.connect(sys.argv[2])
helix_db.migrate_all(conn)
conn.close()
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local hook="$1"
  local payload="$2"
  shift 2
  env "$@" /bin/bash "$HELIX_ROOT/.claude/hooks/$hook" <<<"$payload"
}

agent_slot_count() {
  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
row = conn.execute("SELECT COUNT(*) FROM agent_slots").fetchone()
print(row[0])
conn.close()
PY
}

seed_codex_slots() {
  local count="$1"
  python3 - "$HELIX_ROOT" "$DB_PATH" "$count" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import agent_slots

for index in range(int(sys.argv[3])):
    agent_slots.fire_slot(
        agent_kind="codex",
        role=f"se-{index}",
        session_id="session-codex-slot-check",
    )
PY
}

harness_event_count() {
  local check_name="$1"
  python3 - "$DB_PATH" "$check_name" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
row = conn.execute(
    "SELECT COUNT(*) FROM harness_check_events WHERE check_name = ?",
    (sys.argv[2],),
).fetchone()
print(row[0])
conn.close()
PY
}

write_transcript() {
  TRANSCRIPT_PATH="$TMP_ROOT/transcript.jsonl"
  printf '%s\n' '{"tool_name":"WebSearch","query":"requirements traceability official"}' >"$TRANSCRIPT_PATH"
}

@test "UT-WSC-07: Agent tool + subagent_type は agent_slots に fire 記録する" {
  run run_hook "pretooluse-agent-fire.sh" \
    '{"tool_name":"Agent","tool_input":{"subagent_type":"pmo-haiku"}}' \
    HELIX_SESSION_ID=session-ut-wsc-07
  [ "$status" -eq 0 ]
  [ "$(agent_slot_count)" = "1" ]
}

@test "UT-WSC-07: subagent_type 空なら fire_slot を呼ばず fail-open する" {
  run run_hook "pretooluse-agent-fire.sh" \
    '{"tool_name":"Agent","tool_input":{}}' \
    HELIX_SESSION_ID=session-ut-wsc-07-empty
  [ "$status" -eq 0 ]
  [ "$(agent_slot_count)" = "0" ]
}

@test "UT-WSC-08: Agent guard は subagent_type 未指定を block する" {
  run run_hook "pretooluse-agent-guard.sh" \
    '{"tool_name":"Agent","tool_input":{}}'
  [ "$status" -eq 2 ]
  [[ "$output" == *"subagent_type が指定されていません"* ]]
}

@test "UT-WSC-08: Agent guard は許可 subagent + model 省略を pass する" {
  run run_hook "pretooluse-agent-guard.sh" \
    '{"tool_name":"Agent","tool_input":{"subagent_type":"pmo-haiku"}}'
  [ "$status" -eq 0 ]
}

@test "UT-WSC-10: active slot が 6 以上なら Codex slot warning を記録する" {
  seed_codex_slots 6

  run run_hook "pretooluse-codex-slot-check.sh" \
    '{"tool_name":"Bash","tool_input":{"command":"helix codex --role se --task test"}}'
  [ "$status" -eq 0 ]
  [[ "$output" == *"active slot=6"* ]]
  [ "$(harness_event_count slot_count_warning)" = "1" ]
}

@test "UT-WSC-10: --wbs-id に --reference-doc が無い場合は警告を記録する" {
  run run_hook "pretooluse-codex-slot-check.sh" \
    '{"tool_name":"Bash","tool_input":{"command":"helix codex --role se --task test --wbs-id WBS-001"}}'
  [ "$status" -eq 0 ]
  [[ "$output" == *"--reference-doc も必要"* ]]
  [ "$(harness_event_count wbs_id_without_reference)" = "1" ]
}

@test "UT-WSC-11: ADR 新規作成は WebSearch/WebFetch 証跡なしなら block する" {
  local project_root="$TMP_ROOT/project"
  mkdir -p "$project_root/docs/adr"

  run run_hook "pretooluse-design-doc-web-search-guard.sh" \
    '{"tool_name":"Write","tool_input":{"file_path":"docs/adr/ADR-999-test.md","content":"# Test\n"}}' \
    CLAUDE_PROJECT_DIR="$project_root"
  [ "$status" -eq 2 ]
  [[ "$output" == *"WebSearch / WebFetch"* ]]
}

@test "UT-WSC-11: ADR 新規作成は transcript に WebSearch 証跡があれば pass する" {
  local project_root="$TMP_ROOT/project"
  mkdir -p "$project_root/docs/adr"
  write_transcript

  run run_hook "pretooluse-design-doc-web-search-guard.sh" \
    '{"tool_name":"Write","tool_input":{"file_path":"docs/adr/ADR-999-test.md","content":"# Test\n"}}' \
    CLAUDE_PROJECT_DIR="$project_root" \
    CLAUDE_TRANSCRIPT_PATH="$TRANSCRIPT_PATH"
  [ "$status" -eq 0 ]
}
