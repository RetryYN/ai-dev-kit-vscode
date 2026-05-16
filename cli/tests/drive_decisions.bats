#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" init "$PROJECT_ROOT/.helix/helix.db" >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

seed_entry() {
  local drive="$1"
  local pair_status="$2"
  local raw_meta="${3:-{}}"

  python3 - "$HELIX_ROOT" "$PROJECT_ROOT" "$drive" "$pair_status" "$raw_meta" <<'PY'
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
drive = sys.argv[3]
pair_status = sys.argv[4]
raw_meta = sys.argv[5]
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import helix_db

conn = helix_db.get_connection(project_root / ".helix" / "helix.db")
try:
    conn.execute(
        """
        INSERT INTO design_sprint_entries (
            plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, raw_meta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("PLAN-100", f"{drive}-functional", "functional", "functional", drive, "shared", pair_status, raw_meta),
    )
    conn.commit()
finally:
    conn.close()
PY
}

@test "drive-decision records preserved decision" {
  seed_entry "be" "paired" '{"g2_evidence_preserved": true}'
  seed_entry "fe" "paired" '{"g2_evidence_preserved": true}'

  run "$HELIX_ROOT/cli/helix-plan" drive-decision --plan-id PLAN-100 --from-drive be --to-drive fe
  [ "$status" -eq 0 ]
  [[ "$output" == *'"decision": "preserved"'* ]]

  run python3 - <<'PY' "$PROJECT_ROOT/.helix/helix.db"
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
try:
    row = conn.execute(
        "SELECT decision, reason FROM design_sprint_drive_decisions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row == ("preserved", "pair_status=paired and evidence preserved for be->fe")
finally:
    conn.close()
PY
  [ "$status" -eq 0 ]
}

@test "drive-decision records failed decision for disallowed transition" {
  seed_entry "fullstack" "paired" '{"g2_evidence_preserved": true}'
  seed_entry "fe" "paired" '{"g2_evidence_preserved": true}'

  run "$HELIX_ROOT/cli/helix-plan" drive-decision --plan-id PLAN-100 --from-drive fullstack --to-drive fe
  [ "$status" -eq 0 ]
  [[ "$output" == *'"decision": "failed"'* ]]

  run python3 - <<'PY' "$PROJECT_ROOT/.helix/helix.db"
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
try:
    row = conn.execute(
        "SELECT decision FROM design_sprint_drive_decisions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row == ("failed",)
finally:
    conn.close()
PY
  [ "$status" -eq 0 ]
}

@test "drive-decision warns and continues when decision insert fails" {
  seed_entry "be" "paired" '{"g2_evidence_preserved": true}'
  seed_entry "fe" "paired" '{"g2_evidence_preserved": true}'

  python3 - <<'PY' "$PROJECT_ROOT/.helix/helix.db"
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
try:
    conn.execute(
        """
        CREATE TRIGGER fail_drive_decision_insert
        BEFORE INSERT ON design_sprint_drive_decisions
        BEGIN
            SELECT RAISE(ABORT, 'injected decision failure');
        END
        """
    )
    conn.commit()
finally:
    conn.close()
PY

  run "$HELIX_ROOT/cli/helix-plan" drive-decision --plan-id PLAN-100 --from-drive be --to-drive fe
  [ "$status" -eq 0 ]
  [[ "$output" == *'"decision": "preserved"'* ]]
  [[ "$output" == *"WARNING: design_sprint_drive_decisions write skipped: injected decision failure"* ]]

  run python3 - <<'PY' "$PROJECT_ROOT/.helix/helix.db"
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
try:
    count = conn.execute("SELECT COUNT(*) FROM design_sprint_drive_decisions").fetchone()[0]
    assert count == 0
finally:
    conn.close()
PY
  [ "$status" -eq 0 ]
}
