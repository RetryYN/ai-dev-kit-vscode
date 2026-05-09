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

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: gate-cross-sprint-test
current_phase: L2
sprint:
  drive: be
  ui: false
gates:
  G1:
    status: passed
YAML

  cat > "$PROJECT_ROOT/.helix/gate-checks.yaml" <<'YAML'
G2:
  name: "G2 cross sprint smoke"
  static:
  ai:
YAML

  python3 "$HELIX_ROOT/cli/lib/helix_db.py" init "$PROJECT_ROOT/.helix/helix.db" >/dev/null
  python3 - <<'PY' "$PROJECT_ROOT/.helix/helix.db"
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
try:
    conn.execute(
        """
        INSERT INTO entries (id, axis, stack, lifecycle, sprint_id, ref, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("entry-1", "code", "back", "addition", ".4", "cli/helix-gate", "{}"),
    )
    conn.commit()
finally:
    conn.close()
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix gate G2 --cross-sprint --dry-run saves cross-sprint review" {
  run "$HELIX_ROOT/cli/helix" gate G2 --cross-sprint --dry-run --readiness-mode skip
  [ "$status" -eq 0 ]
  [[ "$output" == *"cross-sprint review"* ]]
  [[ "$output" == *"latest sprint: .4"* ]]
  [[ "$output" == *"=== G2 PASS ==="* ]]

  run bash -lc "ls '$PROJECT_ROOT/.helix/cross-sprint-reviews/'*.json"
  [ "$status" -eq 0 ]

  run python3 - <<'PY' "$PROJECT_ROOT/.helix/cross-sprint-reviews"
import json
import sys
from pathlib import Path

review_dir = Path(sys.argv[1])
files = sorted(review_dir.glob("*.json"))
assert files, "review log missing"
payload = json.loads(files[-1].read_text(encoding="utf-8"))
assert payload["review_type"] == "cross-sprint"
assert payload["latest_completed_sprint"]["value"] == ".4"
assert len(payload["checks"]) == 3
print(payload["summary"]["verdict"])
PY
  [ "$status" -eq 0 ]
  [[ "$output" == "pass" ]]
}
