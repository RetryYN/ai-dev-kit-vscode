#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  FAKE_BIN="$TMP_ROOT/bin"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR" "$FAKE_BIN"
  cd "$PROJECT_ROOT"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$FAKE_BIN:$PATH"
  export HELIX_TEST_TODAY="2026-05-03"
  export HELIX_TEST_TIME="12:34"
  export HELIX_TEST_DB_PATH="$PROJECT_ROOT/.helix/helix.db"
  export HELIX_TEST_SUMMARY_DIR="$TMP_ROOT/session-summaries"
  export HELIX_SESSION_SUMMARY_DIR="$HELIX_TEST_SUMMARY_DIR"
  mkdir -p "$HELIX_TEST_SUMMARY_DIR"

  cat > "$FAKE_BIN/date" <<'SH'
#!/usr/bin/env bash
case "${1:-}" in
  +%Y-%m-%d)
    printf '%s\n' "${HELIX_TEST_TODAY:-2026-05-03}"
    ;;
  '+%Y-%m-%d %H:%M')
    printf '%s %s\n' "${HELIX_TEST_TODAY:-2026-05-03}" "${HELIX_TEST_TIME:-12:34}"
    ;;
  *)
    exec /usr/bin/date "$@"
    ;;
esac
SH
  chmod +x "$FAKE_BIN/date"

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" init "$HELIX_TEST_DB_PATH" >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_session_summary() {
  "$HELIX_ROOT/cli/helix-session-summary"
}

insert_cost_log() {
  local date_value="$1"
  local role="${2:-opus-pm}"
  local model="${3:-claude-opus-4-6}"
  local time_value="${4:-10:00:00}"

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" insert "$HELIX_TEST_DB_PATH" cost_log \
    "{\"role\":\"${role}\",\"model\":\"${model}\",\"thinking\":\"high\",\"created_at\":\"${date_value}T${time_value}\"}" >/dev/null
}

insert_hook_event() {
  local date_value="$1"
  local event_type="$2"
  local time_value="${3:-10:00:00}"

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" insert "$HELIX_TEST_DB_PATH" hook_events \
    "{\"event_type\":\"${event_type}\",\"file\":\"session\",\"result\":\"success\",\"created_at\":\"${date_value}T${time_value}\"}" >/dev/null
}

insert_gate_run() {
  local date_value="$1"
  local gate="$2"
  local result="$3"
  local time_value="${4:-10:00:00}"

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" insert "$HELIX_TEST_DB_PATH" gate_runs \
    "{\"gate\":\"${gate}\",\"result\":\"${result}\",\"fail_reasons\":\"[]\",\"retry_count\":0,\"duration_ms\":12,\"created_at\":\"${date_value}T${time_value}\"}" >/dev/null
}

count_cost_log() {
  python3 - "$HELIX_TEST_DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
try:
    print(conn.execute("SELECT COUNT(*) FROM cost_log").fetchone()[0])
finally:
    conn.close()
PY
}

assert_status_zero() {
  if [[ "$status" -ne 0 ]]; then
    echo "command failed: status=${status} output=${output}" >&2
    exit 1
  fi
}

assert_no_md_files() {
  local count
  count="$(find "$HELIX_TEST_SUMMARY_DIR" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
  if [[ "$count" != "0" ]]; then
    echo "expected no markdown files in $HELIX_TEST_SUMMARY_DIR, found $count" >&2
    find "$HELIX_TEST_SUMMARY_DIR" -maxdepth 1 -name '*.md' -print >&2
    exit 1
  fi
}

@test "PLAN-016 DoD #1: helix-session-summary は md を新規生成しない" {
  run run_session_summary
  assert_status_zero

  assert_no_md_files
}

@test "PLAN-016 DoD #1: 既存 md があってもタイムスタンプを変更しない" {
  local existing_file="$HELIX_TEST_SUMMARY_DIR/2026-05-03-session.md"
  mkdir -p "$(dirname "$existing_file")"
  printf '# existing\n' > "$existing_file"
  touch -t 202605031001.00 "$existing_file"
  local before
  before="$(python3 - "$existing_file" <<'PY'
import os
import sys
print(os.stat(sys.argv[1]).st_mtime_ns)
PY
)"

  run run_session_summary
  assert_status_zero

  local after
  after="$(python3 - "$existing_file" <<'PY'
import os
import sys
print(os.stat(sys.argv[1]).st_mtime_ns)
PY
)"
  [[ "$after" == "$before" ]]
}

@test "PLAN-016 DoD #2: report session --date は任意日付ごとに cost_log を集計する" {
  insert_cost_log "2026-05-03" "opus-pm" "claude-opus-4-6" "10:00:00"
  insert_cost_log "2026-05-03" "claude-code" "claude-code" "10:01:00"
  insert_cost_log "2026-05-04" "opus-pm" "claude-opus-4-6" "11:00:00"

  run "$HELIX_ROOT/cli/helix" log report session --date "2026-05-03"
  assert_status_zero
  [[ "$output" == *"Date: 2026-05-03"* ]]
  [[ "$output" == *"終了 2 回"* ]]
  [[ "$output" == *"claude-code / claude-code: 1"* ]]
  [[ "$output" == *"opus-pm / claude-opus-4-6: 1"* ]]

  run "$HELIX_ROOT/cli/helix" log report session --date "2026-05-04"
  assert_status_zero
  [[ "$output" == *"Date: 2026-05-04"* ]]
  [[ "$output" == *"終了 1 回"* ]]
  [[ "$output" != *"claude-code / claude-code: 1"* ]]
  [[ "$output" == *"opus-pm / claude-opus-4-6: 1"* ]]
}

@test "PLAN-016 DoD #3: hook_events gate_runs cost_log を同日付で集計する" {
  insert_hook_event "2026-05-03" "Stop" "10:00:00"
  insert_hook_event "2026-05-03" "Stop" "10:01:00"
  insert_hook_event "2026-05-04" "Stop" "10:02:00"
  insert_gate_run "2026-05-03" "G4" "passed" "10:03:00"
  insert_gate_run "2026-05-03" "G4" "passed" "10:04:00"
  insert_gate_run "2026-05-04" "G4" "failed" "10:05:00"
  insert_cost_log "2026-05-03" "opus-pm" "claude-opus-4-6" "10:06:00"
  insert_cost_log "2026-05-03" "qa" "gpt-5.4" "10:07:00"
  insert_cost_log "2026-05-04" "qa" "gpt-5.4" "10:08:00"

  run "$HELIX_ROOT/cli/helix" log report session --date "2026-05-03"
  assert_status_zero
  [[ "$output" == *"Stop: 2"* ]]
  [[ "$output" == *"G4 passed: 2"* ]]
  [[ "$output" == *"opus-pm / claude-opus-4-6: 1"* ]]
  [[ "$output" == *"qa / gpt-5.4: 1"* ]]
  [[ "$output" != *"G4 failed: 1"* ]]
}

@test "PLAN-016 DoD #5: 単発実行は exit 0 かつ stdout stderr 0 byte" {
  local stdout_file="$TMP_ROOT/session-summary.stdout"
  local stderr_file="$TMP_ROOT/session-summary.stderr"

  run bash -c '"$1" >"$2" 2>"$3"' _ "$HELIX_ROOT/cli/helix-session-summary" "$stdout_file" "$stderr_file"
  assert_status_zero

  [[ ! -s "$stdout_file" ]]
  [[ ! -s "$stderr_file" ]]
  [[ "$output" == "" ]]
}

@test "PLAN-016 DB INSERT: helix-session-summary は cost_log を 1 件追加する" {
  local before after
  before="$(count_cost_log)"

  run run_session_summary
  assert_status_zero

  after="$(count_cost_log)"
  [[ "$after" -eq "$((before + 1))" ]]
}

@test "PLAN-016 --help: report session への誘導を表示して exit 0" {
  run "$HELIX_ROOT/cli/helix-session-summary" --help
  assert_status_zero
  [[ "$output" == *"使い方: helix session-summary"* ]]
  [[ "$output" == *"helix log report session"* ]]

  run "$HELIX_ROOT/cli/helix-session-summary" -h
  assert_status_zero
  [[ "$output" == *"使い方: helix session-summary"* ]]
  [[ "$output" == *"helix log report session"* ]]
}

@test "PLAN-016 edge: HELIX_TEST_DB_PATH の DB が未存在でも exit 0 で静音" {
  local missing_db="$TMP_ROOT/missing/helix.db"
  local stdout_file="$TMP_ROOT/missing-db.stdout"
  local stderr_file="$TMP_ROOT/missing-db.stderr"
  export HELIX_TEST_DB_PATH="$missing_db"

  run bash -c '"$1" >"$2" 2>"$3"' _ "$HELIX_ROOT/cli/helix-session-summary" "$stdout_file" "$stderr_file"
  assert_status_zero

  [[ ! -e "$missing_db" ]]
  [[ ! -s "$stdout_file" ]]
  [[ ! -s "$stderr_file" ]]
  [[ "$output" == "" ]]
}
