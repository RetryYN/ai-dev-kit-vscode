#!/usr/bin/env bats

# DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-12

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HOOK="$HELIX_ROOT/.claude/hooks/pretooluse-opus-repo-block.sh"
  TMP_ROOT="$(mktemp -d)"
  DB_PATH="$TMP_ROOT/helix.db"
  export HELIX_DB_PATH="$DB_PATH"
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
  local payload="$1"
  shift
  env "$@" "$HOOK" <<<"$payload"
}

audit_row_count() {
  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
row = conn.execute("SELECT COALESCE(MAX(id), 0) FROM audit_log").fetchone()
print(row[0] if row else 0)
conn.close()
PY
}

@test "UT-WSC-12: escape hatch でも reason 未設定なら block を維持する" {
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$HELIX_ROOT/cli/lib/budget.py\"}}" \
    CLAUDE_PROJECT_DIR="$HELIX_ROOT" \
    HELIX_ALLOW_OPUS_REPO_EDIT=1
  [ "$status" -eq 2 ]
  [[ "$output" == *"helix codex"* ]]
}

@test "UT-WSC-12: hook 実行時に audit_log へ hook_exec と gate_eval を記録する" {
  local start_id
  start_id="$(audit_row_count)"

  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$HELIX_ROOT/cli/lib/budget.py\"}}" \
    CLAUDE_PROJECT_DIR="$HELIX_ROOT"
  [ "$status" -eq 2 ]

  run python3 - "$DB_PATH" "$start_id" <<'PY'
import json
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
rows = conn.execute(
    "SELECT audit_kind, actor, payload FROM audit_log WHERE id > ? ORDER BY id",
    (int(sys.argv[2]),),
).fetchall()
conn.close()

assert [row[0] for row in rows] == ["hook_exec", "gate_eval"]
assert rows[0][1] == "pretooluse-opus-repo-block.sh"
hook_payload = json.loads(rows[0][2])
gate_payload = json.loads(rows[1][2])
assert hook_payload["hook_name"] == "pretooluse-opus-repo-block"
assert gate_payload["gate_name"] == "opus_repo_edit_policy"
assert gate_payload["verdict"] == "blocked"
PY
  [ "$status" -eq 0 ]
}
