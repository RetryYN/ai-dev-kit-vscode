#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  TOOL_HELPER="$HELIX_ROOT/cli/tests/_helix-bats-helper.bash"
  HELIX_TMP="$(mktemp -d)"
  TMP_ROOT="$HELIX_TMP"
  source "$TOOL_HELPER"
  helix_bats_mark "$HELIX_TMP"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  DB_PATH="$HELIX_TMP/test_helix.db"

  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR" "$BIN_DIR"
  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "bats@example.com"
  git config user.name "Bats"
  echo "init" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_HOME="$HELIX_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:$HELIX_ROOT/cli:$PATH"
  export HELIX_DB_PATH="$DB_PATH"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"

  python3 - "$HELIX_ROOT" "$DB_PATH" >/dev/null <<'PY'
import sys
import sqlite3

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db
from cli.lib import agent_slots

conn = sqlite3.connect(sys.argv[2])
helix_db.migrate_all(conn)
conn.close()

for _ in range(6):
    slot_id = agent_slots.fire_slot(agent_kind="codex", role="pg", plan_id="PLAN-080", task_id="TASK-080")
    agent_slots.release_slot(slot_id)
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

seed_automation_run() {
  local run_kind="$1"
  local trigger_actor="$2"
  local started_at="$3"
  local status="$4"
  local summary="${5:-}"
  local ended_at="${6:-}"
  local exit_code="${7:-}"

  python3 - "$HELIX_ROOT" "$DB_PATH" "$run_kind" "$trigger_actor" "$started_at" "$status" "$summary" "$ended_at" "$exit_code" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db

db_path, run_kind, trigger_actor, started_at, status, summary, ended_at, exit_code = sys.argv[2:10]
payload = [summary or None, ended_at or None, int(exit_code) if exit_code else None]
with helix_db._write_connection(db_path) as conn:
    conn.execute(
        """
        INSERT INTO automation_runs (
            run_kind, plan_id, trigger_actor, started_at, ended_at, status, exit_code, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_kind,
            "PLAN-080",
            trigger_actor,
            started_at,
            payload[1],
            status,
            payload[2],
            payload[0],
        ),
    )
PY
}

seed_active_slot() {
  local agent_kind="$1"
  local role="$2"
  local plan_id="$3"
  local task_id="$4"
  local sprint="$5"
  local session_id="$6"
  local fired_at="${7:-}"

  python3 - "$HELIX_ROOT" "$DB_PATH" "$agent_kind" "$role" "$plan_id" "$task_id" "$sprint" "$session_id" "$fired_at" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import agent_slots, helix_db

db_path, agent_kind, role, plan_id, task_id, sprint, session_id, fired_at = sys.argv[2:10]
with helix_db._write_connection(db_path) as conn:
    conn.execute(
        """
        INSERT INTO agent_slots (
            slot_key, agent_kind, role, plan_id, task_id, sprint, session_id, fired_at, status, slot_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(NULLIF(?, ''), datetime('now')), 'running', 'helix_codex')
        """,
        (
            agent_slots._build_slot_key(agent_kind, role or None, None),
            agent_kind,
            role or None,
            plan_id or None,
            task_id or None,
            sprint or None,
            session_id or None,
            fired_at,
        ),
    )
PY
}

seed_harness_event() {
  local event_kind="$1"
  local check_name="$2"
  local session_id="$3"
  local severity="$4"
  local payload="$5"

  python3 - "$HELIX_ROOT" "$DB_PATH" "$event_kind" "$check_name" "$session_id" "$severity" "$payload" <<'PY'
import json
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import harness_monitor

db_path, event_kind, check_name, session_id, severity, payload = sys.argv[2:8]
event_id = harness_monitor.record_event(
    event_kind,
    check_name,
    session_id=session_id or None,
    severity=severity,
    payload=json.loads(payload),
    user_visible=True,
)
print(event_id)
PY
}

count_events_by_kind() {
  python3 - "$DB_PATH" "$1" <<'PY'
import sqlite3
import sys

db_path, kind = sys.argv[1:3]
conn = sqlite3.connect(db_path)
row = conn.execute(
    "SELECT COUNT(*) FROM harness_check_events WHERE event_kind = ?",
    (kind,),
).fetchone()
print(row[0])
PY
}

query_event_payload() {
  python3 - "$DB_PATH" "$1" <<'PY'
import sqlite3
import sys

db_path, check_name = sys.argv[1:3]
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
row = conn.execute(
    "SELECT payload FROM harness_check_events WHERE check_name = ? ORDER BY id DESC LIMIT 1",
    (check_name,),
).fetchone()
if row is None:
    raise SystemExit(1)
print(row["payload"])
PY
}

@test "I-CLI-001: helix harness status が active slot と recent event を表示する" {
  seed_automation_run helix-push system "2026-05-17 11:00:00" running '{"phase":"push"}'
  seed_active_slot codex pg PLAN-080 TASK-001 .4 sess-001
  seed_harness_event audit status_viewed sess-001 warning '{"active":1,"slot_count":1}' >/dev/null

  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  run bash -c '"$1" "$2" >"$3" 2>"$4"' _ "$HELIX_ROOT/cli/helix-harness" status "$stdout_file" "$stderr_file"

  [ "$status" -eq 0 ]
  STATUS_STDOUT="$(cat "$stdout_file")"
  STATUS_STDERR="$(cat "$stderr_file")"
  [[ "$STATUS_STDOUT" == *"[Active Slots]"* ]]
  [[ "$STATUS_STDOUT" == *"PLAN-080/TASK-001"* ]]
  [[ "$STATUS_STDOUT" == *"[Recent Warnings]"* ]]
  [[ "$STATUS_STDOUT" == *"status_viewed active=1"* ]]
  [[ "$STATUS_STDOUT" == *"[Peak Parallel Today]"* ]]
  [ -z "$STATUS_STDERR" ]
  [ "$(count_events_by_kind pull)" -eq 1 ]
}

@test "I-CLI-002: helix harness status --json が stable schema で返る" {
  seed_automation_run helix-push system "2026-05-17 11:00:00" running '{"phase":"push"}'
  seed_active_slot codex se PLAN-080 TASK-002 .4 sess-json

  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  run bash -c '"$1" "$2" "$3" >"$4" 2>"$5"' _ "$HELIX_ROOT/cli/helix-harness" status --json "$stdout_file" "$stderr_file"

  [ "$status" -eq 0 ]
  STATUS_STDOUT="$(cat "$stdout_file")"
  STATUS_STDERR="$(cat "$stderr_file")"
  JSON_OUTPUT="$STATUS_STDOUT" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_OUTPUT"])
assert payload["active_slot_count"] == 1, payload
assert payload["peak_parallel_today"] >= 1, payload
assert isinstance(payload["running_tasks"], list), payload
assert isinstance(payload["recent_warnings"], list), payload
assert isinstance(payload["recent_criticals"], list), payload
PY
  [ -z "$STATUS_STDERR" ]
  [ "$(count_events_by_kind pull)" -eq 1 ]
}

@test "I-PUSH-001: pretooluse hook が active slot 閾値で system-reminder を出す" {
  for n in 1 2 3 4 5 6; do
    seed_active_slot codex pg PLAN-080 "TASK-10${n}" .4 sess-push
  done

  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  run bash -c '"$1" >"$2" 2>"$3"' _ "$HELIX_ROOT/.claude/hooks/pretooluse-codex-slot-check.sh" "$stdout_file" "$stderr_file" <<'JSON'
{"tool_name":"Bash","tool_input":{"command":"helix codex --role pg --task PLAN-080"}}
JSON

  [ "$status" -eq 0 ]
  STATUS_STDOUT="$(cat "$stdout_file")"
  STATUS_STDERR="$(cat "$stderr_file")"
  [ -z "$STATUS_STDOUT" ]
  [[ "$STATUS_STDERR" == *"<system-reminder>"* ]]
  [[ "$STATUS_STDERR" == *"8 並列ルールに近い"* ]]
  [ "$(count_events_by_kind push)" -eq 1 ]
  PAYLOAD="$(query_event_payload slot_count_warning)"
  PAYLOAD_JSON="$PAYLOAD" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["PAYLOAD_JSON"])
assert payload["active"] == 6, payload
PY
}

@test "I-PUSH-002: pretooluse hook が --reference-doc 不足を警告する" {
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  run bash -c '"$1" >"$2" 2>"$3"' _ "$HELIX_ROOT/.claude/hooks/pretooluse-codex-slot-check.sh" "$stdout_file" "$stderr_file" <<'JSON'
{"tool_name":"Bash","tool_input":{"command":"helix codex --role pg --task PLAN-080 --wbs-id WBS-001"}}
JSON

  [ "$status" -eq 0 ]
  STATUS_STDOUT="$(cat "$stdout_file")"
  STATUS_STDERR="$(cat "$stderr_file")"
  [ -z "$STATUS_STDOUT" ]
  [[ "$STATUS_STDERR" == *"--reference-doc"* ]]
  [ "$(count_events_by_kind push)" -eq 1 ]
  PAYLOAD="$(query_event_payload wbs_id_without_reference)"
  [ -n "$PAYLOAD" ]
}

@test "I-PUSH-003: non-helix command では hook が無出力のまま終了する" {
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  run bash -c '"$1" >"$2" 2>"$3"' _ "$HELIX_ROOT/.claude/hooks/pretooluse-codex-slot-check.sh" "$stdout_file" "$stderr_file" <<'JSON'
{"tool_name":"Bash","tool_input":{"command":"npm test"}}
JSON

  [ "$status" -eq 0 ]
  STATUS_STDOUT="$(cat "$stdout_file")"
  STATUS_STDERR="$(cat "$stderr_file")"
  [ -z "$STATUS_STDOUT" ]
  [ -z "$STATUS_STDERR" ]
  [ "$(count_events_by_kind push)" -eq 0 ]
}

@test "I-AUDIT-001: sessionstart hook が release miss と critical event を要約する" {
  stale_at="$(python3 - <<'PY'
from datetime import datetime, timedelta
print((datetime.utcnow() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"))
PY
)"
  seed_active_slot codex se PLAN-080 TASK-900 .4 sess-audit "$stale_at"
  seed_harness_event audit carry_summary sess-audit critical '{"carry":{"severity":"critical"}}' >/dev/null

  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  run bash -c '"$1" >"$2" 2>"$3"' _ "$HELIX_ROOT/.claude/hooks/sessionstart-harness-summary.sh" "$stdout_file" "$stderr_file"

  [ "$status" -eq 0 ]
  STATUS_STDOUT="$(cat "$stdout_file")"
  STATUS_STDERR="$(cat "$stderr_file")"
  [[ "$STATUS_STDOUT" == *"release 漏れ slot: 1 件"* ]]
  [[ "$STATUS_STDOUT" == *"critical event: 1 件"* ]]
  [ -z "$STATUS_STDERR" ]
}
