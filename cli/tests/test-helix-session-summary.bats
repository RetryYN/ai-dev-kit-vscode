#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  trap 'rm -rf "$TMP_ROOT"' EXIT
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

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" init "$PROJECT_ROOT/.helix/helix.db" >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT"
}

run_session_summary() {
  "$HELIX_ROOT/cli/helix-session-summary"
}

summary_file() {
  printf '%s/.helix/session-summaries/%s-session.md\n' "$PROJECT_ROOT" "$1"
}

new_header_count() {
  local file="$1"
  grep -cE '^## [0-9]{4}-[0-9]{2}-[0-9]{2} セッション \(最終更新' "$file" || true
}

date_header_count() {
  local date_value="$1"
  local file="$2"
  grep -cE "^## ${date_value} セッション \\(最終更新" "$file" || true
}

insert_cost_log() {
  local date_value="$1"
  python3 "$HELIX_ROOT/cli/lib/helix_db.py" insert "$PROJECT_ROOT/.helix/helix.db" cost_log \
    "{\"role\":\"opus-pm\",\"model\":\"claude-opus-4-6\",\"thinking\":\"high\",\"created_at\":\"${date_value}T10:00:00\"}" >/dev/null
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local message="$3"
  if [[ "$actual" != "$expected" ]]; then
    echo "${message}: expected=${expected} actual=${actual}" >&2
    exit 1
  fi
}

assert_ge() {
  local minimum="$1"
  local actual="$2"
  local message="$3"
  if (( actual < minimum )); then
    echo "${message}: expected>=${minimum} actual=${actual}" >&2
    exit 1
  fi
}

assert_status_zero() {
  if [[ "$status" -ne 0 ]]; then
    echo "command failed: status=${status} output=${output}" >&2
    exit 1
  fi
}

assert_file_exists() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "missing file: $file" >&2
    exit 1
  fi
}

@test "DoD #1: same-day five Stop hooks produce one current-day block" {
  local today="2026-05-03"
  local file
  file="$(summary_file "$today")"

  for _ in 1 2 3 4 5; do
    run run_session_summary
    assert_status_zero
  done

  assert_file_exists "$file"
  assert_eq "1" "$(new_header_count "$file")" "current-day block count"
}

@test "DoD #2: two mocked days create independent files with one block each" {
  local day1="2026-05-03"
  local day2="2026-05-04"
  local file1 file2
  file1="$(summary_file "$day1")"
  file2="$(summary_file "$day2")"

  export HELIX_TEST_TODAY="$day1"
  for _ in 1 2 3; do
    run run_session_summary
    assert_status_zero
  done

  export HELIX_TEST_TODAY="$day2"
  for _ in 1 2 3; do
    run run_session_summary
    assert_status_zero
  done

  assert_file_exists "$file1"
  assert_file_exists "$file2"
  assert_eq "1" "$(date_header_count "$day1" "$file1")" "${day1} block count"
  assert_eq "1" "$(date_header_count "$day2" "$file2")" "${day2} block count"
}

@test "DoD #3: finished count equals one when no fixture rows exist" {
  local today="2026-05-03"
  local file inserted_today_count actual_count
  file="$(summary_file "$today")"

  run run_session_summary
  assert_status_zero

  if python3 "$HELIX_ROOT/cli/lib/helix_db.py" query "$PROJECT_ROOT/.helix/helix.db" "SELECT 1" >/dev/null 2>&1; then
    inserted_today_count="$(python3 "$HELIX_ROOT/cli/lib/helix_db.py" query "$PROJECT_ROOT/.helix/helix.db" \
      "SELECT COUNT(*) FROM cost_log WHERE role='opus-pm' AND date(created_at)='${today}'" 2>/dev/null | tail -1)"
  elif command -v sqlite3 >/dev/null 2>&1; then
    inserted_today_count="$(sqlite3 "$PROJECT_ROOT/.helix/helix.db" "SELECT COUNT(*) FROM cost_log WHERE role='opus-pm' AND date(created_at)='${today}'")"
  else
    inserted_today_count="$(python3 - "$PROJECT_ROOT/.helix/helix.db" "$today" <<'PY'
import sqlite3
import sys

db_path, today = sys.argv[1:]
conn = sqlite3.connect(db_path)
try:
    print(conn.execute("SELECT COUNT(*) FROM cost_log WHERE role='opus-pm' AND date(created_at)=?", (today,)).fetchone()[0])
finally:
    conn.close()
PY
)"
  fi
  assert_eq "1" "$inserted_today_count" "cost_log rows for mocked today"

  assert_file_exists "$file"
  actual_count="$(grep -oE '終了 [0-9]+ 回' "$file" | grep -oE '[0-9]+' || true)"
  assert_eq "1" "$actual_count" "finished count"
}

@test "DoD #4: legacy session-ended headings are preserved and new block is added" {
  local today="2026-05-03"
  local file legacy_count
  file="$(summary_file "$today")"
  mkdir -p "$(dirname "$file")"
  cat > "$file" <<'MD'
# Session Summary

## セッション終了: 2026-04-30 23:50

legacy body
MD

  run run_session_summary
  assert_status_zero

  legacy_count="$(grep -c '^## セッション終了:' "$file" || true)"
  assert_ge "1" "$legacy_count" "legacy heading count"
  assert_eq "1" "$(date_header_count "$today" "$file")" "new-format current-day block count"
}

@test "DoD #6: concurrent Stop hook invocations do not corrupt summary" {
  local today="2026-05-03"
  local file out1 out2 pid1 pid2 status1 status2 combined_output size tmp_count
  file="$(summary_file "$today")"
  out1="$TMP_ROOT/concurrent-1.out"
  out2="$TMP_ROOT/concurrent-2.out"
  export HELIX_TEST_TODAY="$today"

  python3 - "$PROJECT_ROOT/.helix/helix.db" "$today" <<'PY'
import sqlite3
import sys

db_path, today = sys.argv[1:]
conn = sqlite3.connect(db_path)
rows = [
    ("opus-pm", "claude-opus-4-6", "high", f"{today}T10:{i % 60:02d}:00")
    for i in range(150000)
]
conn.executemany(
    "INSERT INTO cost_log (role, model, thinking, created_at) VALUES (?, ?, ?, ?)",
    rows,
)
conn.commit()
conn.close()
PY

  ( run_session_summary >"$out1" 2>&1 ) &
  pid1=$!
  ( run_session_summary >"$out2" 2>&1 ) &
  pid2=$!

  status1=0
  wait "$pid1" || status1=$?
  status2=0
  wait "$pid2" || status2=$?

  assert_eq "0" "$status1" "first concurrent process exit status"
  assert_eq "0" "$status2" "second concurrent process exit status"

  combined_output="$(cat "$out1" "$out2")"
  if [[ "$combined_output" != *"lock busy"* ]]; then
    echo "expected lock busy message in concurrent output: ${combined_output}" >&2
    exit 1
  fi

  assert_file_exists "$file"
  size="$(wc -c < "$file" | tr -d ' ')"
  assert_ge "1" "$size" "summary file size"
  assert_eq "1" "$(date_header_count "$today" "$file")" "block count after concurrent run"

  tmp_count="$(find "$(dirname "$file")" -maxdepth 1 -name "$(basename "$file").tmp.*" 2>/dev/null | wc -l | tr -d ' ')"
  assert_eq "0" "$tmp_count" "leftover tmp files"
}
