#!/usr/bin/env bats
# PLAN-083 Phase 3: stop hook 自動 release テスト

setup() {
  export HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  export HELIX_TMP="$(mktemp -d)"
  export HELIX_DB_PATH="$HELIX_TMP/test_helix.db"
  export HELIX_SESSION_ID="stop-test-83"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  unset CLAUDE_SESSION_ID

  python3 - "$HELIX_ROOT" "$HELIX_DB_PATH" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db

helix_db.init_db(sys.argv[2])
PY
}

teardown() {
  rm -rf "$HELIX_TMP"
  unset HELIX_ROOT HELIX_DB_PATH HELIX_SESSION_ID CLAUDE_SESSION_ID PYTHONPATH
}

count_running_slots() {
  local session_id="$1"
  python3 - "$HELIX_ROOT" "$HELIX_DB_PATH" "$session_id" <<'PY'
import json
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import agent_slots

session_id = sys.argv[3]
slots = [slot for slot in agent_slots.list_active_slots() if slot.get("session_id") == session_id]
print(len(slots))
PY
}

@test "I-STOP-REL-001: stop-hook releases running slots of current session" {
  python3 - "$HELIX_ROOT" "$HELIX_DB_PATH" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import agent_slots

agent_slots.fire_slot(agent_kind='claude_subagent', subagent_type='pmo-sonnet', session_id='stop-test-83')
agent_slots.fire_slot(agent_kind='claude_subagent', subagent_type='pmo-haiku', session_id='stop-test-83')
agent_slots.fire_slot(agent_kind='claude_subagent', subagent_type='pmo-tech-fork', session_id='other-session')
PY

  run "$HELIX_ROOT/cli/helix-stop-hook"
  [ "$status" -eq 0 ]

  count="$(count_running_slots stop-test-83)"
  [ "$count" = "0" ]

  count_other="$(count_running_slots other-session)"
  [ "$count_other" = "1" ]
}

@test "I-STOP-REL-002: stop-hook with no running slots exit 0" {
  run "$HELIX_ROOT/cli/helix-stop-hook"
  [ "$status" -eq 0 ]
}

@test "I-STOP-REL-003: stop-hook still updates handover/CURRENT.json (regression)" {
  run "$HELIX_ROOT/cli/helix-stop-hook"
  [ "$status" -eq 0 ]
  [[ "$output" == *"handover"* || "$output" == *"revision"* || "$output" == *"updated"* ]]
}

@test "I-STOP-REL-004: stop-hook with HELIX_SESSION_ID unset uses fallback" {
  unset HELIX_SESSION_ID
  run "$HELIX_ROOT/cli/helix-stop-hook"
  [ "$status" -eq 0 ]
}
