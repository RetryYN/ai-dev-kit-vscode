#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  ORIG_PWD="$PWD"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  TOOL_ROOT="$TMP_ROOT/tool"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  DB_PATH="$PROJECT_ROOT/.helix/helix.db"

  mkdir -p "$TOOL_ROOT" "$PROJECT_ROOT/.helix" "$HOME_DIR" "$BIN_DIR"
  cp -R "$HELIX_ROOT/cli" "$TOOL_ROOT/cli"
  ln -s "$TOOL_ROOT/cli" "$PROJECT_ROOT/cli"

  export HELIX_HOME="$TOOL_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:/usr/bin:/bin"
  cd "$PROJECT_ROOT"

  init_legacy_db
}

teardown() {
  cd "$ORIG_PWD"
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

init_legacy_db() {
  HOME="$HOME_DIR" HELIX_HOME="$TOOL_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" python3 - <<'PY'
import os
import sys

sys.path.insert(0, os.path.join(os.environ["HELIX_HOME"], "cli", "lib"))
import helix_db

db_path = os.path.join(os.environ["HELIX_PROJECT_ROOT"], ".helix", "helix.db")
with helix_db._write_connection(db_path) as conn:
    helix_db.migrate_all(conn)
PY
}

write_push_gate_module() {
  cat > "$TOOL_ROOT/cli/lib/push_gate.py" <<'EOF'
def run_all_gates(**kwargs):
    return 0
EOF
}

write_push_helper() {
  cat > "$TOOL_ROOT/cli/lib/mock_push_helper.sh" <<'EOF'
#!/usr/bin/env bash
echo "mock push helper"
exit 0
EOF
  chmod +x "$TOOL_ROOT/cli/lib/mock_push_helper.sh"
}

latest_automation_run_json() {
  HOME="$HOME_DIR" HELIX_HOME="$TOOL_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" python3 - <<'PY'
import json
import os
import sqlite3

db_path = os.path.join(os.environ["HELIX_PROJECT_ROOT"], ".helix", "helix.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
row = conn.execute(
    "SELECT run_kind, status, exit_code, summary FROM automation_runs ORDER BY id DESC LIMIT 1"
).fetchone()
if row is None:
    raise SystemExit("automation_runs row not found")
payload = dict(row)
payload["summary"] = json.loads(payload["summary"]) if payload["summary"] else None
print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
PY
}

seed_agent_slot() {
  HOME="$HOME_DIR" HELIX_HOME="$TOOL_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" python3 - <<'PY'
import os
import sys

sys.path.insert(0, os.path.join(os.environ["HELIX_HOME"], "cli", "lib"))
import agent_slots

agent_slots.fire_slot("codex", role="se", plan_id="PLAN-084", sprint=".A.4")
PY
}

# DoD 検証: PLAN-084-integration-test-design.md I-SMOKE-001
@test "I-SMOKE-001: helix-pr legacy automation_runs smoke stays green on helix.db" {
  write_push_gate_module

  run "$TOOL_ROOT/cli/helix-pr" --gate --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Gate validation completed (dry-run); PR creation skipped."* ]]

  row_json="$(latest_automation_run_json)"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["run_kind"] == "pr"
assert row["status"] == "completed"
assert row["exit_code"] == 0
assert row["summary"]["trigger_source"] == "helix-pr"
assert row["summary"]["dry_run"] is True
assert row["summary"]["gate"] is True
PY
}

# DoD 検証: PLAN-084-integration-test-design.md I-SMOKE-002
@test "I-SMOKE-002: helix-push legacy automation_runs smoke stays green on helix.db" {
  write_push_helper

  run env HELIX_PUSH_HELPER="$TOOL_ROOT/cli/lib/mock_push_helper.sh" "$TOOL_ROOT/cli/helix-push" --gate

  [ "$status" -eq 0 ]
  [[ "$output" == *"mock push helper"* ]]

  row_json="$(latest_automation_run_json)"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["run_kind"] == "push"
assert row["status"] == "completed"
assert row["exit_code"] == 0
assert row["summary"]["trigger_source"] == "helix-push"
assert row["summary"]["execute"] is False
assert row["summary"]["remote"] == "origin"
assert row["summary"]["branch"] == "main"
PY
}

# DoD 検証: PLAN-084-integration-test-design.md I-SMOKE-003
@test "I-SMOKE-003: helix-agent slots reads seeded legacy slot data" {
  seed_agent_slot

  run "$TOOL_ROOT/cli/helix-agent" slots --all --json

  [ "$status" -eq 0 ]
  OUTPUT_JSON="$output" python3 - <<'PY'
import json
import os

rows = json.loads(os.environ["OUTPUT_JSON"])
assert len(rows) == 1
assert rows[0]["agent_kind"] == "codex"
assert rows[0]["role"] == "se"
assert rows[0]["plan_id"] == "PLAN-084"
assert rows[0]["sprint"] == ".A.4"
PY
}

# DoD 検証: PLAN-084-integration-test-design.md I-SMOKE-004
@test "I-SMOKE-004: helix-pr push agent sequence preserves legacy single-db compatibility" {
  write_push_gate_module
  write_push_helper
  seed_agent_slot

  run "$TOOL_ROOT/cli/helix-pr" --gate --dry-run
  [ "$status" -eq 0 ]

  run env HELIX_PUSH_HELPER="$TOOL_ROOT/cli/lib/mock_push_helper.sh" "$TOOL_ROOT/cli/helix-push" --gate
  [ "$status" -eq 0 ]

  run "$TOOL_ROOT/cli/helix-agent" slots --all --json
  [ "$status" -eq 0 ]
  [[ "$output" == *"PLAN-084"* ]]
}

# DoD 検証: PLAN-084-integration-test-design.md I-SMOKE-005
@test "I-SMOKE-005: dual-write smoke is deferred until Phase 4.A.2+" {
  skip "dual-write (HELIX_DB_CUTOVER=0 で旧 helix.db と分離 db の同時書込) は未実装"
}

# DoD 検証: PLAN-084-integration-test-design.md I-SMOKE-006
@test "I-SMOKE-006: cutover smoke is deferred until top-level CLI routing is enabled" {
  skip "HELIX_DB_CUTOVER=1 でも top-level CLI は legacy db_path を明示指定しており分離 db へ切替わらない"
}
