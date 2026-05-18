#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOOK="$REPO_ROOT/.claude/hooks/posttooluse-design-doc-web-search-revert.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

PROJECT_ROOT="$TMP_ROOT/project"
TRANSCRIPT_DIR="$TMP_ROOT/transcripts"
BACKUP_DIR="$TMP_ROOT/backups"
DB_PATH="$TMP_ROOT/helix.db"

run_hook() {
  local payload="$1"
  shift
  env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_SESSION_ID="sess-post-001" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$TRANSCRIPT_DIR" \
    HELIX_DESIGN_DOC_GUARD_DB_PATH="$DB_PATH" \
    HELIX_DESIGN_DOC_REVERT_BACKUP_DIR="$BACKUP_DIR" \
    "$@" \
    "$HOOK" <<<"$payload"
}

reset_case() {
  rm -rf "$PROJECT_ROOT" "$TRANSCRIPT_DIR" "$BACKUP_DIR"
  mkdir -p "$PROJECT_ROOT/docs/adr" "$PROJECT_ROOT/docs/plans" "$TRANSCRIPT_DIR" "$BACKUP_DIR"
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

add_web_transcript() {
  cat >"$TRANSCRIPT_DIR/web.jsonl" <<'EOF'
{"tool_name":"WebSearch","tool_input":{"query":"design doc guardrail"}}
EOF
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

reset_case

# T1: PreToolUse pass 想定 (research evidence あり) + PostToolUse pass
target="$PROJECT_ROOT/docs/plans/PLAN-901-pass.md"
printf '# pass\n' >"$target"
add_web_transcript
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T1 research evidence keeps file"
assert_exists "$target" "T1 target survives"

# T2: PreToolUse block 想定 + PostToolUse revert
reset_case
target="$PROJECT_ROOT/docs/plans/PLAN-902-revert.md"
printf '# revert\n' >"$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 1 "$status" "T2 missing research triggers revert"
assert_not_exists "$target" "T2 target reverted"
backup_file="$(find "$BACKUP_DIR" -type f | head -n 1 || true)"
assert_exists "$backup_file" "T2 backup created"
if [[ "$output" != *"revert"* ]]; then
  echo "FAIL: T2 expected revert message" >&2
  exit 1
fi

# T3: bypass 有効
reset_case
target="$PROJECT_ROOT/docs/adr/ADR-903-bypass.md"
printf '# bypass\n' >"$target"
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 HELIX_DESIGN_DOC_NO_WEB_REASON='manual investigation documented elsewhere' 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T3 bypass passes"
assert_exists "$target" "T3 target survives"

# T4: 既存 file 編集は revert skip (small edit pass)
reset_case
target="$PROJECT_ROOT/docs/adr/ADR-904-existing.md"
cat >"$target" <<'EOF'
# title
line1
line2
EOF
(
  cd "$PROJECT_ROOT"
  git add docs/adr/ADR-904-existing.md
  git commit -qm "seed existing design doc"
)
cat >"$target" <<'EOF'
# title
line1
line2 updated
EOF
payload="$(payload_for_write "$target")"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T4 tracked small edit skips revert"
assert_exists "$target" "T4 target survives"
if [[ "$(cat "$target")" != $'# title\nline1\nline2 updated' ]]; then
  echo "FAIL: T4 content changed unexpectedly" >&2
  exit 1
fi

echo "4/4 PASS"
