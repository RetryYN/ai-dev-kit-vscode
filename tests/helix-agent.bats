#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  TOOL_HELPER="$HELIX_ROOT/cli/tests/_helix-bats-helper.bash"
  TMP_ROOT="$(mktemp -d)"
  source "$TOOL_HELPER"
  helix_bats_mark "$TMP_ROOT"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  DB_PATH="$PROJECT_ROOT/.helix/helix.db"

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

sys.path.insert(0, sys.argv[1])
from cli.lib import helix_db

helix_db.init_db(sys.argv[2])
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_fake_codex() {
  local exit_code="${1:-0}"
  local sleep_seconds="${2:-0}"
  local mode="${3:-default}"

  cat > "$BIN_DIR/codex" <<EOF
#!/usr/bin/env bash
set -u
FAKE_CODEX_EXIT_CODE="${exit_code}"
FAKE_CODEX_SLEEP="${sleep_seconds}"
FAKE_CODEX_MODE="${mode}"
TMP_ROOT="${TMP_ROOT}"
PROJECT_ROOT="${PROJECT_ROOT}"

printf '%s\n' "\$*" >> "\$TMP_ROOT/codex.args"

if [[ "\$FAKE_CODEX_MODE" == "running_count" ]]; then
  python3 - "\$PROJECT_ROOT/.helix/helix.db" "\$TMP_ROOT/running-count" <<'PY'
import sqlite3
import sys

db_path, out_path = sys.argv[1:3]
conn = sqlite3.connect(db_path)
row = conn.execute(
    "SELECT COUNT(*) FROM agent_slots WHERE status = 'running' AND released_at IS NULL"
).fetchone()
with open(out_path, "w", encoding="utf-8") as fh:
  fh.write(str(row[0]))
PY
fi

if [[ "\$FAKE_CODEX_MODE" == "signal_parent" ]]; then
  parent_shell=\$(ps -o ppid= -p "\$PPID" 2>/dev/null | tr -d '[:space:]')
  kill -INT "\$PPID" 2>/dev/null || true
  if [[ "\$parent_shell" =~ ^[0-9]+$ ]]; then
    kill -INT "\$parent_shell" 2>/dev/null || true
  fi
  exit 0
fi

if [[ "\$FAKE_CODEX_MODE" == "signal_probe" ]]; then
  printf '%s\n' "\$\$" > "\$TMP_ROOT/codex.pid"
fi

trap 'exit 130' INT
trap 'exit 143' TERM

if [[ "\$FAKE_CODEX_SLEEP" != "0" ]]; then
  sleep "\$FAKE_CODEX_SLEEP"
fi

printf 'fake codex ok\n'
exit "\$FAKE_CODEX_EXIT_CODE"
EOF
  chmod +x "$BIN_DIR/codex"
}

slot_row_json() {
  local slot_id="$1"
  python3 - "$DB_PATH" "$slot_id" <<'PY'
import json
import sqlite3
import sys

db_path, slot_id = sys.argv[1], int(sys.argv[2])
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM agent_slots WHERE id = ?", (slot_id,)).fetchone()
if row is None:
    raise SystemExit(1)
print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
PY
}

slot_count() {
  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
row = conn.execute("SELECT COUNT(*) FROM agent_slots").fetchone()
print(row[0])
PY
}

set_slot_fired_at_seconds_ago() {
  local slot_id="$1"
  local seconds_ago="$2"
  python3 - "$DB_PATH" "$slot_id" "$seconds_ago" <<'PY'
import datetime
import sqlite3
import sys

db_path, slot_id, seconds_ago = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fired_at = (datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds_ago)).strftime("%Y-%m-%d %H:%M:%S")
conn = sqlite3.connect(db_path)
conn.execute("UPDATE agent_slots SET fired_at = ? WHERE id = ?", (fired_at, slot_id))
conn.commit()
PY
}

fire_slot() {
  local agent_kind="${1:-codex}"
  local role="${2:-tl}"
  local plan_id="${3:-PLAN-078}"
  local task_id="${4:-TASK-001}"
  local sprint="${5:-.4}"

  run "$HELIX_ROOT/cli/helix-agent" fire \
    --agent-kind "$agent_kind" \
    --role "$role" \
    --plan-id "$plan_id" \
    --task-id "$task_id" \
    --sprint "$sprint"
}

release_slot() {
  local slot_id="$1"
  local status="$2"
  local exit_code="${3:-}"

  if [[ -n "$exit_code" ]]; then
    run "$HELIX_ROOT/cli/helix-agent" release --slot-id "$slot_id" --status "$status" --exit-code "$exit_code"
  else
    run "$HELIX_ROOT/cli/helix-agent" release --slot-id "$slot_id" --status "$status"
  fi
}

@test "I-CLI-001: helix-agent fire で running slot id を返す" {
  fire_slot codex tl PLAN-078 TASK-001 .4

  [ "$status" -eq 0 ]
  [[ "$output" =~ ^[0-9]+$ ]]

  slot_json="$(slot_row_json "$output")"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["SLOT_JSON"])
assert row["agent_kind"] == "codex", row
assert row["role"] == "tl", row
assert row["plan_id"] == "PLAN-078", row
assert row["task_id"] == "TASK-001", row
assert row["sprint"] == ".4", row
assert row["status"] == "running", row
assert row["released_at"] is None, row
assert row["slot_source"] == "helix_codex", row
PY
}

@test "I-CLI-002: helix-agent release completed で終了状態を保存する" {
  fire_slot codex se PLAN-078 TASK-002 .4
  slot_id="$output"

  release_slot "$slot_id" completed 0
  [ "$status" -eq 0 ]

  slot_json="$(slot_row_json "$slot_id")"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["SLOT_JSON"])
assert row["status"] == "completed", row
assert row["exit_code"] == 0, row
assert row["released_at"], row
PY
}

@test "I-CLI-003: helix-agent release failed で exit_code を保存する" {
  fire_slot codex qa PLAN-078 TASK-003 .4
  slot_id="$output"

  release_slot "$slot_id" failed 7
  [ "$status" -eq 0 ]

  slot_json="$(slot_row_json "$slot_id")"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["SLOT_JSON"])
assert row["status"] == "failed", row
assert row["exit_code"] == 7, row
assert row["released_at"], row
PY
}

@test "I-CLI-004: helix-agent release cancelled で cancelled を保存する" {
  fire_slot codex pg PLAN-078 TASK-004 .4
  slot_id="$output"

  release_slot "$slot_id" cancelled
  [ "$status" -eq 0 ]

  slot_json="$(slot_row_json "$slot_id")"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["SLOT_JSON"])
assert row["status"] == "cancelled", row
assert row["exit_code"] is None, row
assert row["released_at"], row
PY
}

@test "I-CLI-006: helix-agent fire は無効な agent_kind を拒否する" {
  run "$HELIX_ROOT/cli/helix-agent" fire --agent-kind unknown --role tl

  [ "$status" -ne 0 ]
  [[ "$output" == *"invalid agent_kind"* ]]
  [ "$(slot_count)" -eq 0 ]
}

@test "I-CLI-007: helix-agent slots --active は table 見出しを出力する" {
  fire_slot codex tl PLAN-078 TASK-007 .4
  slot_id="$output"
  fire_slot codex se PLAN-078 TASK-008 .4
  other_slot_id="$output"
  release_slot "$other_slot_id" completed 0
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-agent" slots --active
  [ "$status" -eq 0 ]
  [[ "$output" == *"ID | AGENT | ROLE | STATUS | FIRED_AT | PLAN | TASK | SPRINT | SOURCE"* ]]
  [[ "$output" == *"$slot_id"* ]]
  [[ "$output" != *"$other_slot_id"* ]]
  [[ "$output" == *"running"* ]]
}

@test "I-CLI-008: helix-agent slots --all --json は JSON 配列を返す" {
  fire_slot codex tl PLAN-078 TASK-009 .4
  running_slot="$output"
  fire_slot codex se PLAN-078 TASK-010 .4
  completed_slot="$output"
  release_slot "$completed_slot" completed 0
  [ "$status" -eq 0 ]
  fire_slot codex qa PLAN-079 TASK-011 .4
  failed_slot="$output"
  release_slot "$failed_slot" failed 3
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-agent" slots --all --json
  [ "$status" -eq 0 ]

  JSON_PAYLOAD="$output" python3 - <<'PY'
import json
import os

rows = json.loads(os.environ["JSON_PAYLOAD"])
statuses = {row["status"] for row in rows}
assert statuses == {"running", "completed", "failed"}, rows
assert any(row["id"] for row in rows), rows
assert all("slot_source" in row for row in rows), rows
PY
}

@test "I-CLI-009: helix-agent slots --stale は 5 分境界を含める" {
  fire_slot codex tl PLAN-078 TASK-012 .4
  old_slot="$output"
  fire_slot codex tl PLAN-078 TASK-013 .4
  boundary_slot="$output"
  fire_slot codex tl PLAN-078 TASK-014 .4
  recent_slot="$output"

  set_slot_fired_at_seconds_ago "$old_slot" 301
  set_slot_fired_at_seconds_ago "$boundary_slot" 300
  set_slot_fired_at_seconds_ago "$recent_slot" 299

  run "$HELIX_ROOT/cli/helix-agent" slots --stale
  [ "$status" -eq 0 ]
  [[ "$output" == *"$old_slot"* ]]
  [[ "$output" == *"$boundary_slot"* ]]
  [[ "$output" != *"$recent_slot"* ]]
}

@test "I-CLI-010: helix-agent stats --by hour は table で peak_parallel を出す" {
  fire_slot codex tl PLAN-078 TASK-015 .4
  slot_a="$output"
  release_slot "$slot_a" completed 0
  [ "$status" -eq 0 ]
  fire_slot codex se PLAN-078 TASK-016 .4
  slot_b="$output"
  release_slot "$slot_b" failed 2
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-agent" stats --days 1 --by hour
  [ "$status" -eq 0 ]
  [[ "$output" == *"GROUP | TOTAL | PEAK | AVG_S | RUNNING | COMPLETED | FAILED | CANCELLED"* ]]
  [[ "$output" =~ [0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]][0-9]{2}:00:00 ]]
  [[ "$output" == *" | 2 | "* ]]
}

@test "I-CLI-011: helix-agent stats --by role --json は role 別 JSON を返す" {
  fire_slot codex tl PLAN-078 TASK-017 .4
  slot_tl="$output"
  release_slot "$slot_tl" completed 0
  [ "$status" -eq 0 ]
  fire_slot codex se PLAN-078 TASK-018 .4
  slot_se="$output"
  release_slot "$slot_se" failed 1
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-agent" stats --days 7 --by role --json
  [ "$status" -eq 0 ]

  JSON_PAYLOAD="$output" python3 - <<'PY'
import json
import os

rows = json.loads(os.environ["JSON_PAYLOAD"])
groups = {row["group"] for row in rows}
assert groups == {"tl", "se"}, rows
assert all("peak_parallel" in row for row in rows), rows
assert all("total" in row for row in rows), rows
PY
}

@test "I-CLI-012: helix-agent stats --by plan_id は plan ごとに行を分ける" {
  fire_slot codex tl PLAN-078 TASK-019 .4
  plan_078_slot="$output"
  release_slot "$plan_078_slot" completed 0
  [ "$status" -eq 0 ]
  fire_slot codex tl PLAN-079 TASK-020 .4
  plan_079_slot="$output"
  release_slot "$plan_079_slot" completed 0
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-agent" stats --days 7 --by plan_id
  [ "$status" -eq 0 ]
  [[ "$output" == *"GROUP | TOTAL | PEAK | AVG_S | RUNNING | COMPLETED | FAILED | CANCELLED"* ]]
  [[ "$output" == *"PLAN-078"* ]]
  [[ "$output" == *"PLAN-079"* ]]
}

@test "I-WRAP-001: helix-codex は exec 前に slot を fire する" {
  write_fake_codex 0 0 running_count

  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "wrap smoke"
  [ "$status" -eq 0 ]
  [[ "$output" == *"fake codex ok"* ]]
  [ "$(cat "$TMP_ROOT/running-count")" -eq 1 ]
}

@test "I-WRAP-002: helix-codex 正常終了時は completed で release する" {
  write_fake_codex 0 0

  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "wrap success"
  [ "$status" -eq 0 ]
  [[ "$output" == *"fake codex ok"* ]]

  [ "$(slot_count)" -eq 1 ]
  slot_json="$(python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM agent_slots ORDER BY id DESC LIMIT 1").fetchone()
print(dict(row))
PY
)"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import ast
import os

row = ast.literal_eval(os.environ["SLOT_JSON"])
assert row["status"] == "completed", row
assert row["exit_code"] == 0, row
assert row["released_at"], row
PY
}

@test "I-WRAP-003: helix-codex 異常終了時は failed で release する" {
  write_fake_codex 2 0

  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "wrap failure"
  [ "$status" -eq 2 ]
  [[ "$output" == *"fake codex ok"* ]]

  slot_json="$(python3 - "$DB_PATH" <<'PY'
import json
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM agent_slots ORDER BY id DESC LIMIT 1").fetchone()
print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
PY
)"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["SLOT_JSON"])
assert row["status"] == "failed", row
assert row["exit_code"] == 2, row
assert row["released_at"], row
PY
}

@test "I-WRAP-004: helix-codex は SIGINT で cancelled に遷移する" {
  write_fake_codex 0 0 signal_parent

  setsid "$HELIX_ROOT/cli/helix-codex" --role tl --task "wrap interrupt" >"$TMP_ROOT/wrap-interrupt.out" 2>&1 &
  wrapper_pid=$!
  set +e
  wait "$wrapper_pid"
  wrapper_status=$?
  set -e
  [ "$wrapper_status" -eq 130 ]

  slot_json="$(python3 - "$DB_PATH" <<'PY'
import json
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM agent_slots ORDER BY id DESC LIMIT 1").fetchone()
print(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
PY
)"
  SLOT_JSON="$slot_json" python3 - <<'PY'
import json
import os

row = json.loads(os.environ["SLOT_JSON"])
assert row["status"] == "cancelled", row
assert row["released_at"], row
PY
}

@test "I-WRAP-006: helix-codex --no-record は slot を作らない" {
  write_fake_codex 0 0

  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "wrap no record" --no-record
  [ "$status" -eq 0 ]
  [ "$(slot_count)" -eq 0 ]
}
