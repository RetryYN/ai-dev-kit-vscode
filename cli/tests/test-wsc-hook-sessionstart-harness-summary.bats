#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-13

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/sessionstart-harness-summary.sh"
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

seed_stale_slot() {
  local fired_at="$1"
  python3 - "$HELIX_ROOT" "$DB_PATH" "$fired_at" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import agent_slots, helix_db

db_path, fired_at = sys.argv[2:4]
with helix_db._write_connection(db_path) as conn:
    conn.execute(
        """
        INSERT INTO agent_slots (
            slot_key, agent_kind, role, plan_id, task_id, sprint, session_id, fired_at, status, slot_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', 'helix_codex')
        """,
        (
            agent_slots._build_slot_key("codex", "se", None),
            "codex",
            "se",
            "PLAN-080",
            "TASK-080",
            ".4",
            "session-stale",
            fired_at,
        ),
    )
PY
}

seed_critical_event() {
  python3 - "$HELIX_ROOT" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from cli.lib import harness_monitor

harness_monitor.record_event(
    "audit",
    "carry_summary",
    session_id="session-critical",
    severity="critical",
    payload={"carry": {"severity": "critical"}},
    user_visible=True,
)
PY
}

@test "UT-WSC-13: stale slot があれば release 推奨を出す" {
  local stale_at
  stale_at="$(python3 - <<'PY'
from datetime import datetime, timedelta
print((datetime.utcnow() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"))
PY
)"
  seed_stale_slot "$stale_at"

  run /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"release 漏れ slot: 1 件"* ]]
  [[ "$output" != *"critical event"* ]]
}

@test "UT-WSC-13: critical event のみでも要約を出す" {
  seed_critical_event

  run /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"critical event: 1 件"* ]]
  [[ "$output" != *"release 漏れ slot"* ]]
}

@test "UT-WSC-13: stale/critical が無ければ無出力で終わる" {
  run /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "UT-WSC-13: timeout/exception 相当でも fail-open で無出力になる" {
  mkdir -p "$TMP_ROOT/bin"
  cat >"$TMP_ROOT/bin/timeout" <<'EOF'
#!/bin/sh
exit 1
EOF
  chmod +x "$TMP_ROOT/bin/timeout"

  run env PATH="$TMP_ROOT/bin:/usr/bin:/bin" HELIX_DB_PATH="$DB_PATH" /bin/bash "$HOOK"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
