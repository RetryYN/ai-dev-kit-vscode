#!/usr/bin/env bats
# PLAN-083 Phase 2: pretooluse-agent-fire.sh 結合テスト

setup() {
  export HELIX_TMP="$(mktemp -d)"
  export HELIX_DB_PATH="$HELIX_TMP/test_helix.db"
  export HELIX_SESSION_ID="test-session-83"
  python3 -c "
import sqlite3
from cli.lib import helix_db
conn = sqlite3.connect('$HELIX_DB_PATH')
helix_db.migrate_all(conn)
conn.close()
"
  chmod +x .claude/hooks/pretooluse-agent-fire.sh 2>/dev/null || true
}

teardown() {
  rm -rf "$HELIX_TMP"
  unset HELIX_SESSION_ID
}

_slot_count() {
  local where="${1:-1=1}"
  python3 -c "
import sqlite3, os, sys
conn = sqlite3.connect(os.environ['HELIX_DB_PATH'])
where_clause = sys.argv[1]
c = conn.execute('SELECT COUNT(*) FROM agent_slots WHERE ' + where_clause).fetchone()[0]
print(c)
conn.close()
" "$where"
}

@test "I-PUSH-FIRE-001: Agent tool with subagent_type fires agent_slots" {
  input='{"tool_name":"Agent","tool_input":{"subagent_type":"pmo-sonnet","description":"test"}}'
  run bash -c "printf '%s' '$input' | ./.claude/hooks/pretooluse-agent-fire.sh"
  [ "$status" -eq 0 ]
  count=$(_slot_count "subagent_type='pmo-sonnet' AND session_id='test-session-83'")
  [ "$count" = "1" ]
}

@test "I-PUSH-FIRE-002: Non-Agent tool is ignored" {
  input='{"tool_name":"Bash","tool_input":{"command":"ls"}}'
  run bash -c "printf '%s' '$input' | ./.claude/hooks/pretooluse-agent-fire.sh"
  [ "$status" -eq 0 ]
  count=$(_slot_count "1=1")
  [ "$count" = "0" ]
}

@test "I-PUSH-FIRE-003: Agent without subagent_type is skipped" {
  input='{"tool_name":"Agent","tool_input":{}}'
  run bash -c "printf '%s' '$input' | ./.claude/hooks/pretooluse-agent-fire.sh"
  [ "$status" -eq 0 ]
  count=$(_slot_count "1=1")
  [ "$count" = "0" ]
}

@test "I-PUSH-FIRE-004: Invalid stdin JSON returns exit 0" {
  run bash -c "echo 'invalid json' | ./.claude/hooks/pretooluse-agent-fire.sh"
  [ "$status" -eq 0 ]
}

@test "I-PUSH-FIRE-005: Multiple Agent calls fire separate slots" {
  for sub in pmo-sonnet pmo-helix-explorer pmo-tech-fork; do
    input="{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$sub\"}}"
    bash -c "printf '%s' '$input' | ./.claude/hooks/pretooluse-agent-fire.sh"
  done
  count=$(_slot_count "session_id='test-session-83'")
  [ "$count" = "3" ]
}

@test "I-PUSH-FIRE-006: HELIX_HARNESS_DEBUG=1 outputs system-reminder" {
  input='{"tool_name":"Agent","tool_input":{"subagent_type":"pmo-sonnet"}}'
  run bash -c "HELIX_HARNESS_DEBUG=1 printf '%s' '$input' | HELIX_HARNESS_DEBUG=1 ./.claude/hooks/pretooluse-agent-fire.sh 2>&1"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Agent fire"* ]]
}

@test "I-PUSH-FIRE-007: session_id fallback from env when session_helper unavailable" {
  input='{"tool_name":"Agent","tool_input":{"subagent_type":"pmo-haiku"}}'
  run bash -c "HELIX_SESSION_ID=fallback-83 printf '%s' '$input' | HELIX_SESSION_ID=fallback-83 ./.claude/hooks/pretooluse-agent-fire.sh"
  [ "$status" -eq 0 ]
  count=$(_slot_count "session_id='fallback-83'")
  [ "$count" -ge "1" ]
}
