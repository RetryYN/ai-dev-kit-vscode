#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

create_trigger_doc() {
  mkdir -p "$PROJECT_ROOT/docs/features/billing"
  cat > "$PROJECT_ROOT/docs/features/billing/D-API.md" <<'MD'
# D-API
- 未確定: 契約詳細は要確認
- KPI 逸脱: 監視指標の再確認が必要
MD
}

seed_old_pending_trigger() {
  python3 - <<'PY' "$HELIX_ROOT" "$PROJECT_ROOT"
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import scrum_trigger

scrum_trigger.save_to_db(
    [
        {
            "scrum_type": "unit",
            "source_id": "docs/features/ttl/D-API.md",
            "artifact_ref": "D-API",
            "event_type": "uncertainty_marker",
            "detected_at": "2026-04-20T00:00:00Z",
            "last_seen_at": "2026-04-20T00:00:00Z",
            "ttl_at": "2026-04-27T00:00:00Z",
            "uncertainty_score": 3,
            "impact_score": 3,
            "confidence": 0.8,
            "evidence_count": 1,
            "normalized_signature": "ttl-pending",
            "content_hash": "ttl-hash",
            "status": "pending",
            "reason_code": "uncertainty_marker",
            "evidence_path_hint": "docs/features/ttl/D-API.md:1-1",
            "source_path": "docs/features/ttl/D-API.md",
            "source_line_start": 1,
            "source_line_end": 1,
            "created_by": "bats",
            "created_at": "2026-04-20T00:00:00Z",
        }
    ],
    project_root / ".helix" / "helix.db",
)
PY
}

first_trigger_id() {
  python3 - <<'PY' "$PROJECT_ROOT"
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1]) / ".helix" / "helix.db"
conn = sqlite3.connect(db_path)
try:
    print(conn.execute("SELECT trigger_id FROM scrum_trigger LIMIT 1").fetchone()[0])
finally:
    conn.close()
PY
}

@test "helix scrum trigger detect returns zero for empty docs directory" {
  mkdir -p "$PROJECT_ROOT/docs/features"

  run "$HELIX_ROOT/cli/helix" scrum trigger detect --scan docs/features

  [ "$status" -eq 0 ]
  [[ "$output" == *"detected: 0"* ]]
}

@test "helix scrum trigger detect --save inserts into helix.db" {
  create_trigger_doc

  run "$HELIX_ROOT/cli/helix" scrum trigger detect --scan docs/features --save

  [ "$status" -eq 0 ]
  [[ "$output" == *"saved: inserted="* ]]

  run python3 - <<'PY' "$PROJECT_ROOT"
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1]) / ".helix" / "helix.db"
conn = sqlite3.connect(db_path)
try:
    count = conn.execute("SELECT COUNT(*) FROM scrum_trigger").fetchone()[0]
    assert count >= 1, count
finally:
    conn.close()
PY
  [ "$status" -eq 0 ]
}

@test "helix scrum trigger list prints empty state" {
  run "$HELIX_ROOT/cli/helix" scrum trigger list

  [ "$status" -eq 0 ]
  [[ "$output" == *"(empty)"* ]]
}

@test "helix scrum trigger list --status pending filters saved triggers" {
  create_trigger_doc
  "$HELIX_ROOT/cli/helix" scrum trigger detect --scan docs/features --save >/dev/null

  run "$HELIX_ROOT/cli/helix" scrum trigger list --status pending

  [ "$status" -eq 0 ]
  [[ "$output" == *"pending"* ]]
}

@test "helix scrum trigger transition moves pending to triaged" {
  create_trigger_doc
  "$HELIX_ROOT/cli/helix" scrum trigger detect --scan docs/features --save >/dev/null
  trigger_id="$(first_trigger_id)"

  run "$HELIX_ROOT/cli/helix" scrum trigger transition --id "$trigger_id" --status triaged --owner PM --reason "reviewed"

  [ "$status" -eq 0 ]
  [[ "$output" == *"transitioned: $trigger_id triaged"* ]]
}

@test "helix scrum trigger transition rejects invalid lifecycle jump" {
  create_trigger_doc
  "$HELIX_ROOT/cli/helix" scrum trigger detect --scan docs/features --save >/dev/null
  trigger_id="$(first_trigger_id)"

  run "$HELIX_ROOT/cli/helix" scrum trigger transition --id "$trigger_id" --status adopted --owner PM

  [ "$status" -eq 2 ]
  [[ "$output" == *"invalid transition"* ]]
}

@test "helix scrum trigger ttl --apply applies pending escalation" {
  seed_old_pending_trigger

  run "$HELIX_ROOT/cli/helix" scrum trigger ttl --apply

  [ "$status" -eq 0 ]
  [[ "$output" == *"pending -> triaged"* ]]
}
