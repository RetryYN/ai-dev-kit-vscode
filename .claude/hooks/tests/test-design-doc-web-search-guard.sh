#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOOK="$REPO_ROOT/.claude/hooks/pretooluse-design-doc-web-search-guard.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

PROJECT_ROOT="$TMP_ROOT/project"
TRANSCRIPT_DIR="$TMP_ROOT/transcripts"
DB_PATH="$TMP_ROOT/helix.db"
mkdir -p "$PROJECT_ROOT/docs/adr" "$PROJECT_ROOT/docs/plans" "$TRANSCRIPT_DIR"

run_hook() {
  local payload="$1"
  shift
  env \
    CLAUDE_PROJECT_DIR="$PROJECT_ROOT" \
    HELIX_SESSION_ID="sess-guard-001" \
    HELIX_DESIGN_DOC_GUARD_TRANSCRIPT_DIR="$TRANSCRIPT_DIR" \
    HELIX_DESIGN_DOC_GUARD_DB_PATH="$DB_PATH" \
    "$@" \
    "$HOOK" <<<"$payload"
}

reset_evidence() {
  rm -rf "$TRANSCRIPT_DIR"
  mkdir -p "$TRANSCRIPT_DIR"
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

add_web_transcript() {
  cat >"$TRANSCRIPT_DIR/web.jsonl" <<'EOF'
{"tool_name":"WebSearch","tool_input":{"query":"design doc guardrail"}}
EOF
}

add_subagent_slot() {
  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.execute(
    "INSERT INTO agent_slots (session_id, subagent_type) VALUES (?, ?)",
    ("sess-guard-001", "pmo-tech-fork"),
)
conn.commit()
conn.close()
PY
}

payload_for_write() {
  local path="$1"
  local content="$2"
  python3 - "$path" "$content" <<'PY'
import json
import sys

path, content = sys.argv[1], sys.argv[2]
print(json.dumps({
    "tool_name": "Write",
    "tool_input": {
        "file_path": path,
        "content": content,
    },
}, ensure_ascii=False))
PY
}

reset_evidence

# T1: 対象外 path → pass
payload="$(payload_for_write "$PROJECT_ROOT/README.md" $'hello\n')"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T1 non-target path"

# T2: 対象 path + Web 検索なし + 新規 file → block
reset_evidence
payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-999-test.md" $'# x\n')"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 2 "$status" "T2 new plan without research"

# T3: 対象 path + Web 検索あり + 新規 file → pass
reset_evidence
add_web_transcript
payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-999-test.md" $'# x\n')"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T3 new plan with web transcript"

# T4: 対象 path + Web 検索なし + 既存 file 小 edit (<50 行) → pass
reset_evidence
cat >"$PROJECT_ROOT/docs/adr/ADR-999-test.md" <<'EOF'
# title
line1
line2
EOF
payload="$(payload_for_write "$PROJECT_ROOT/docs/adr/ADR-999-test.md" $'# title\nline1\nline2 updated\n')"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T4 small edit without research"

# T5: 対象 path + Web 検索なし + 既存 file 大幅変更 (>50 行) → block
reset_evidence
python3 - "$PROJECT_ROOT/docs/plans/PLAN-999-large.md" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.write_text("\n".join(f"before-{i}" for i in range(80)) + "\n", encoding="utf-8")
PY
large_content="$(python3 - <<'PY'
print("\\n".join(f"after-{i}" for i in range(80)) + "\\n")
PY
)"
payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-999-large.md" "$large_content")"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 2 "$status" "T5 large edit without research"

# T6: bypass + 理由あり → pass
reset_evidence
payload="$(payload_for_write "$PROJECT_ROOT/docs/plans/PLAN-999-bypass.md" $'# bypass\n')"
set +e
output="$(run_hook "$payload" HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 HELIX_DESIGN_DOC_NO_WEB_REASON='hotfix doc follow-up' 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T6 bypass with reason"

# T7: pmo-tech-fork subagent 起動済 + 対象 path 新規 → pass
reset_evidence
add_subagent_slot
payload="$(payload_for_write "$PROJECT_ROOT/docs/adr/ADR-999-subagent.md" $'# subagent\n')"
set +e
output="$(run_hook "$payload" 2>&1)"
status=$?
set -e
assert_status 0 "$status" "T7 subagent evidence"

echo "7/7 PASS"
