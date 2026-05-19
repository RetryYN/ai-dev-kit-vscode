#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOOK="$REPO_ROOT/.claude/hooks/posttooluse-design-doc-web-search-revert.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

PROJECT_ROOT="$TMP_ROOT/project"
TRANSCRIPT_DIR="$TMP_ROOT/transcripts"
DB_PATH="$TMP_ROOT/helix.db"

run_hook() {
  local payload="$1"
  shift
  env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$TRANSCRIPT_DIR" \
    HELIX_DESIGN_DOC_GUARD_DB_PATH="$DB_PATH" \
    "$@" \
    bash "$HOOK" <<<"$payload"
}

reset_case() {
  rm -rf "$PROJECT_ROOT" "$TRANSCRIPT_DIR" "$DB_PATH"
  mkdir -p \
    "$PROJECT_ROOT/docs/adr" \
    "$PROJECT_ROOT/docs/architecture" \
    "$PROJECT_ROOT/docs/plans" \
    "$PROJECT_ROOT/docs/specs" \
    "$TRANSCRIPT_DIR"
  (
    cd "$PROJECT_ROOT"
    git init -q
    git config user.email "test@example.com"
    git config user.name "Test User"
    git commit --allow-empty -qm "init"
  )
  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
if db_path.exists():
    db_path.unlink()
conn = sqlite3.connect(str(db_path))
conn.execute(
    """
    CREATE TABLE agent_slots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      subagent_type TEXT
    )
    """
)
conn.commit()
conn.close()
PY
}

assert_status() {
  local expected="$1"
  local actual="$2"
  local label="$3"
  if [[ "$expected" != "$actual" ]]; then
    echo "FAIL: $label expected status=$expected actual=$actual" >&2
    exit 1
  fi
  echo "PASS: $label"
}

assert_contains() {
  local text="$1"
  local needle="$2"
  local label="$3"
  if [[ "$text" != *"$needle"* ]]; then
    echo "FAIL: $label missing text=$needle" >&2
    exit 1
  fi
}

json_field() {
  local text="$1"
  local field="$2"
  python3 - "$text" "$field" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
value = payload
for part in sys.argv[2].split("."):
    if isinstance(value, dict):
        value = value.get(part, "")
    else:
        value = ""
        break
if isinstance(value, (dict, list)):
    print(json.dumps(value, ensure_ascii=False))
else:
    print("" if value is None else value)
PY
}

assert_json_field_equals() {
  local text="$1"
  local field="$2"
  local expected="$3"
  local label="$4"
  local actual
  actual="$(json_field "$text" "$field")"
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL: $label expected $field=$expected actual=$actual" >&2
    exit 1
  fi
}

assert_json_field_matches() {
  local text="$1"
  local field="$2"
  local pattern="$3"
  local label="$4"
  local actual
  actual="$(json_field "$text" "$field")"
  if [[ ! "$actual" =~ $pattern ]]; then
    echo "FAIL: $label invalid $field=$actual pattern=$pattern" >&2
    exit 1
  fi
}

assert_exists() {
  local path="$1"
  local label="$2"
  if [[ ! -e "$path" ]]; then
    echo "FAIL: $label missing path=$path" >&2
    exit 1
  fi
}

assert_not_exists() {
  local path="$1"
  local label="$2"
  if [[ -e "$path" ]]; then
    echo "FAIL: $label unexpected path=$path" >&2
    exit 1
  fi
}

payload_for_write() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys

path = sys.argv[1]
print(json.dumps({
    "tool_name": "Write",
    "tool_input": {
        "file_path": path,
    },
}, ensure_ascii=False))
PY
}

add_web_transcript() {
  cat >"$TRANSCRIPT_DIR/web.jsonl" <<'EOF'
{"session_id":"sess-post-001","tool_name":"WebSearch","tool_input":{"query":"design doc guardrail"}}
EOF
}

create_large_frontmatter_doc() {
  local path="$1"
  python3 - "$path" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = ["---", "title: Smoke", "---", ""]
lines.extend(f"line {idx:03d}" for idx in range(1, 121))
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

reset_case

# T1: session_id missing -> exit 1 + warn, revert なし
target="$PROJECT_ROOT/docs/plans/PLAN-901-session-missing.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID= 2>&1)"
status=$?
set -e
assert_status 1 "$status" "T1 session_id missing skips verification"
assert_json_field_equals "$output" "action" "warn" "T1 action"
assert_json_field_equals "$output" "reason" "session_id_missing" "T1 reason"
assert_exists "$target" "T1 target survives"

# T2: session_id 取得 + bypass env + 履歴 0 件 -> exit 1
reset_case
target="$PROJECT_ROOT/docs/adr/ADR-902-bypass-with-reason.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 HELIX_ALLOW_DESIGN_DOC_NO_WEB_REASON='documented elsewhere' 2>&1)"
status=$?
set -e
assert_status 1 "$status" "T2 bypass with reason warns"
assert_json_field_equals "$output" "reason" "bypass_allowed" "T2 reason"
assert_exists "$target" "T2 target survives"

# T3: session_id 取得 + bypass env なし + 履歴 0 件 + 行数 100+ -> exit 2
reset_case
target="$PROJECT_ROOT/docs/plans/PLAN-903-revert.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 2>&1)"
status=$?
set -e
assert_status 2 "$status" "T3 missing history triggers revert"
assert_not_exists "$target" "T3 target reverted"
assert_json_field_equals "$output" "action" "block" "T3 action"
assert_json_field_equals "$output" "reason" "web_search_history_empty" "T3 reason"

# T4: session_id 取得 + 履歴 1+ 件 -> exit 0
reset_case
target="$PROJECT_ROOT/docs/specs/SPEC-904-history.md"
create_large_frontmatter_doc "$target"
add_web_transcript
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T4 web history passes"
assert_json_field_equals "$output" "action" "pass" "T4 action"
assert_json_field_equals "$output" "reason" "verification_passed" "T4 reason"
assert_exists "$target" "T4 target survives"

# T5: bypass env だけ設定 + reason 空 -> exit 1 + warn
reset_case
target="$PROJECT_ROOT/docs/plans/PLAN-905-bypass-no-reason.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 2>&1)"
status=$?
set -e
assert_status 1 "$status" "T5 bypass without reason stays safe"
assert_json_field_equals "$output" "reason" "bypass_reason_missing" "T5 reason"
assert_exists "$target" "T5 target survives"

# T6: backup ファイル生成確認
reset_case
target="$PROJECT_ROOT/docs/adr/ADR-906-backup.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 2>&1)"
status=$?
set -e
assert_status 2 "$status" "T6 revert produces backup"
backup_file="$(find "$PROJECT_ROOT/.helix/backups" -type f -name 'posttooluse-revert-*-ADR-906-backup.md.bak' | head -n 1 || true)"
assert_exists "$backup_file" "T6 backup created"
assert_json_field_equals "$output" "backup" "$backup_file" "T6 backup field"

# T7: matcher 外 file -> skip exit 0
reset_case
target="$PROJECT_ROOT/docs/architecture/overview.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T7 non-matcher path skips"
assert_json_field_equals "$output" "reason" "skip_non_target_path" "T7 reason"
assert_exists "$target" "T7 target survives"

# T8: exit 2 時は JSON で action=block / reason を返す
reset_case
target="$PROJECT_ROOT/docs/specs/SPEC-907-json-block.md"
create_large_frontmatter_doc "$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_SESSION_ID=sess-post-001 2>&1)"
status=$?
set -e
assert_status 2 "$status" "T8 block returns JSON"
assert_json_field_equals "$output" "action" "block" "T8 action"
assert_json_field_equals "$output" "reason" "web_search_history_empty" "T8 reason"

# T9: reason field は空でなく snake_case
assert_json_field_matches "$output" "reason" '^[A-Za-z0-9_]+$' "T9 reason pattern"

echo "9/9 PASS"
