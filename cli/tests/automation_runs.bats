#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  TOOL_ROOT="$TMP_ROOT/tool"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  DB_PATH="$PROJECT_ROOT/.helix/helix.db"

  mkdir -p "$TOOL_ROOT" "$PROJECT_ROOT" "$HOME_DIR" "$BIN_DIR"
  cp -R "$HELIX_ROOT/cli" "$TOOL_ROOT/cli"

  export HELIX_HOME="$TOOL_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:/usr/bin:/bin"

  init_git_project
  write_mock_gh
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

init_git_project() {
  git init -q "$PROJECT_ROOT"
  git -C "$PROJECT_ROOT" config user.email "qa@example.com"
  git -C "$PROJECT_ROOT" config user.name "QA"
  echo "base" > "$PROJECT_ROOT/README.md"
  git -C "$PROJECT_ROOT" add README.md
  git -C "$PROJECT_ROOT" commit -q -m "feat: base"
  git -C "$PROJECT_ROOT" branch -M main
  git -C "$PROJECT_ROOT" checkout -q -b feature/automation-runs
  echo "change" >> "$PROJECT_ROOT/README.md"
  git -C "$PROJECT_ROOT" add README.md
  git -C "$PROJECT_ROOT" commit -q -m "feat: add automation runs"
  mkdir -p "$PROJECT_ROOT/.helix"
}

write_mock_gh() {
  cat > "$BIN_DIR/gh" <<'EOF'
#!/usr/bin/env bash
echo "gh $*" >&2
exit 0
EOF
  chmod +x "$BIN_DIR/gh"
}

write_push_helper() {
  local exit_code="$1"
  cat > "$TOOL_ROOT/cli/lib/mock_push_helper.sh" <<EOF
#!/usr/bin/env bash
echo "mock push helper"
exit ${exit_code}
EOF
  chmod +x "$TOOL_ROOT/cli/lib/mock_push_helper.sh"
}

write_push_gate_module() {
  local mode="$1"
  cat > "$TOOL_ROOT/cli/lib/push_gate.py" <<EOF
def run_all_gates(**kwargs):
    return ${mode}
EOF
}

latest_run_json() {
  python3 - <<'PY' "$DB_PATH"
import json
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
row = conn.execute(
    "SELECT id, run_kind, trigger_actor, status, exit_code, summary, last_error, ended_at "
    "FROM automation_runs ORDER BY id DESC LIMIT 1"
).fetchone()
if row is None:
    raise SystemExit("no automation_runs row found")
payload = dict(row)
payload["summary"] = json.loads(payload["summary"]) if payload["summary"] else None
print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
PY
}

@test "helix-push records completed automation run" {
  write_push_helper 0

  run env HELIX_PUSH_HELPER="$TOOL_ROOT/cli/lib/mock_push_helper.sh" "$TOOL_ROOT/cli/helix-push" --gate
  [ "$status" -eq 0 ]
  [[ "$output" == *"mock push helper"* ]]

  row_json="$(latest_run_json)"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["run_kind"] == "push"
assert row["trigger_actor"] == "system"
assert row["status"] == "completed"
assert row["exit_code"] == 0
assert row["ended_at"]
assert row["last_error"] is None
assert row["summary"]["trigger_source"] == "helix-push"
assert row["summary"]["execute"] is False
assert row["summary"]["branch"] == "feature/automation-runs"
assert row["summary"]["remote"] == "origin"
PY
}

@test "helix-push keeps running when automation logging fails" {
  write_push_helper 0

  run env HELIX_DB_PATH="$PROJECT_ROOT/.helix" HELIX_PUSH_HELPER="$TOOL_ROOT/cli/lib/mock_push_helper.sh" "$TOOL_ROOT/cli/helix-push" --gate
  [ "$status" -eq 0 ]
  [[ "$output" == *"mock push helper"* ]]
  [[ "$output" == *"WARN: automation_runs start failed for helix-push"* ]]
}

@test "helix-pr records completed automation run on dry-run gate flow" {
  write_push_gate_module 0

  run "$TOOL_ROOT/cli/helix-pr" --gate --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Gate validation completed (dry-run); PR creation skipped."* ]]

  row_json="$(latest_run_json)"
  ROW_JSON="$row_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["ROW_JSON"])
assert row["run_kind"] == "pr"
assert row["trigger_actor"] == "system"
assert row["status"] == "completed"
assert row["exit_code"] == 0
assert row["ended_at"]
assert row["summary"]["trigger_source"] == "helix-pr"
assert row["summary"]["dry_run"] is True
assert row["summary"]["gate"] is True
assert row["summary"]["base"] == "main"
PY
}
