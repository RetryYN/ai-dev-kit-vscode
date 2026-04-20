#!/usr/bin/env bats

setup() {
  REPO_ROOT="/home/tenni/ai-dev-kit-vscode"
  TMP_ROOT="$(mktemp -d)"
  DB_PATH="$TMP_ROOT/legacy-v6.db"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

create_v6_db() {
  DB_PATH="$DB_PATH" python3 - <<'PY'
import os
import sqlite3

db_path = os.environ["DB_PATH"]
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
conn.execute("INSERT INTO schema_version (version, applied_at) VALUES (6, datetime('now'))")
conn.execute(
    """
    CREATE TABLE skill_usage (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_text TEXT NOT NULL,
      skill_id TEXT NOT NULL,
      references_used TEXT,
      agent_used TEXT,
      match_score REAL,
      match_reason TEXT,
      outcome TEXT,
      user_feedback TEXT,
      result_stdout TEXT,
      result_stderr TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      completed_at TIMESTAMP
    )
    """
)
conn.execute("CREATE INDEX idx_skill_usage_skill ON skill_usage(skill_id)")
conn.execute("CREATE INDEX idx_skill_usage_outcome ON skill_usage(outcome)")
conn.execute(
    "INSERT INTO skill_usage (task_text, skill_id, outcome, result_stdout, result_stderr) VALUES (?, ?, ?, ?, ?)",
    ("legacy task", "common/testing", "ok", "stdout", "stderr"),
)
conn.commit()
conn.close()
PY
}

migrate_to_v7() {
  REPO_ROOT="$REPO_ROOT" DB_PATH="$DB_PATH" python3 - <<'PY'
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.environ["REPO_ROOT"], "cli/lib"))
import helix_db

conn = sqlite3.connect(os.environ["DB_PATH"])
helix_db.migrate(conn)
conn.close()
PY
}

@test "v7 migration forward: version=7 と新カラム追加" {
  create_v6_db
  run migrate_to_v7
  [ "$status" -eq 0 ]
  run DB_PATH="$DB_PATH" python3 - <<'PY'
import os
import sqlite3

conn = sqlite3.connect(os.environ["DB_PATH"])
version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
cols = {r[1] for r in conn.execute("PRAGMA table_info(skill_usage)")}
conn.close()
required = {"effort_estimated", "effort_actual", "timeout_occurred", "tokens_used", "model_used", "fallback_applied"}
assert version == 7, version
assert required.issubset(cols), cols
PY
  [ "$status" -eq 0 ]
}

@test "skill_usage 新カラムに INSERT/SELECT 可能" {
  create_v6_db
  migrate_to_v7
  run DB_PATH="$DB_PATH" python3 - <<'PY'
import os
import sqlite3

conn = sqlite3.connect(os.environ["DB_PATH"])
conn.execute(
    "INSERT INTO skill_usage (task_text, skill_id, effort_estimated, timeout_occurred) VALUES (?, ?, ?, ?)",
    ("new task", "common/coding", "high", 1),
)
row = conn.execute(
    "SELECT effort_estimated, timeout_occurred FROM skill_usage WHERE task_text = ?",
    ("new task",),
).fetchone()
conn.commit()
conn.close()
assert row == ("high", 1), row
PY
  [ "$status" -eq 0 ]
}

@test "budget_events テーブル CRUD 動作" {
  create_v6_db
  migrate_to_v7
  run DB_PATH="$DB_PATH" python3 - <<'PY'
import os
import sqlite3

conn = sqlite3.connect(os.environ["DB_PATH"])
conn.execute(
    "INSERT INTO budget_events (occurred_at, event_type, model, pct_used, details_json) VALUES (datetime('now'), ?, ?, ?, ?)",
    ("fallback", "gpt-5.3-codex", 92.5, '{"reason":"threshold"}'),
)
event_id = conn.execute("SELECT id FROM budget_events ORDER BY id DESC LIMIT 1").fetchone()[0]
conn.execute("UPDATE budget_events SET pct_used = ? WHERE id = ?", (95.0, event_id))
updated = conn.execute("SELECT event_type, pct_used FROM budget_events WHERE id = ?", (event_id,)).fetchone()
conn.execute("DELETE FROM budget_events WHERE id = ?", (event_id,))
remaining = conn.execute("SELECT COUNT(*) FROM budget_events WHERE id = ?", (event_id,)).fetchone()[0]
conn.commit()
conn.close()
assert updated == ("fallback", 95.0), updated
assert remaining == 0, remaining
PY
  [ "$status" -eq 0 ]
}

@test "既存 skill_usage レコード数保持 + 新カラム互換" {
  create_v6_db
  migrate_to_v7
  run DB_PATH="$DB_PATH" python3 - <<'PY'
import os
import sqlite3

conn = sqlite3.connect(os.environ["DB_PATH"])
count = conn.execute("SELECT COUNT(*) FROM skill_usage").fetchone()[0]
row = conn.execute(
    "SELECT effort_estimated, tokens_used, model_used, timeout_occurred, fallback_applied FROM skill_usage WHERE task_text = ?",
    ("legacy task",),
).fetchone()
conn.close()
assert count == 1, count
assert row[0] is None and row[1] is None and row[2] is None, row
assert row[3] == 0 and row[4] == 0, row
PY
  [ "$status" -eq 0 ]
}
