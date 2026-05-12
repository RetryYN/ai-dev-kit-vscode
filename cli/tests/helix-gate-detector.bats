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
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export HELIX_DISABLE_FEEDBACK=1

  cat > "$PROJECT_ROOT/.helix/gate-checks.yaml" <<'YAML'
G2:
  name: "G2 detector integration"
  static:
  ai:
G4:
  name: "G4 detector integration"
  static:
  ai:
G6:
  name: "G6 detector integration"
  static:
  ai:
YAML

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
current_phase: L6
sprint:
  drive: be
  ui: false
gates:
  G1:
    status: passed
  G2:
    status: passed
  G3:
    status: passed
  G4:
    status: passed
  G5:
    status: passed
YAML
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

seed_db_case() {
  local mode="$1"
  python3 - "$PROJECT_ROOT/.helix/helix.db" "$mode" <<'PY'
import json
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
mode = sys.argv[2]
db_path.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(db_path))
try:
    conn.executescript(
        """
        CREATE TABLE detector_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            axis_id TEXT NOT NULL,
            detector_name TEXT NOT NULL,
            phase_gate TEXT,
            verdict TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            cost_ms INTEGER NOT NULL,
            raw_json TEXT NOT NULL,
            config_json TEXT NOT NULL,
            command TEXT NOT NULL,
            db_path TEXT NOT NULL
        );
        CREATE TABLE code_index (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            summary TEXT NOT NULL,
            path TEXT NOT NULL,
            line_no INTEGER NOT NULL,
            symbol_line INTEGER NOT NULL DEFAULT 0,
            bucket TEXT NOT NULL DEFAULT 'coverage_eligible'
        );
        CREATE TABLE routing_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT,
            source TEXT,
            decision TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    if mode == "g2":
        conn.executemany(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("sample.load_data", "cli/lib", "snake", "cli/lib/mixed.py", 1, 1, "coverage_eligible"),
                ("sample.loadData", "cli/lib", "camel", "cli/lib/mixed.py", 2, 2, "coverage_eligible"),
            ],
        )
    elif mode == "g4":
        conn.execute(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("sample.orphan", "cli/lib", "orphan", "cli/lib/orphan.py", 1, 1, "coverage_eligible"),
        )
    elif mode == "g6":
        conn.executemany(
            """
            INSERT INTO routing_decisions (plan_id, source, decision, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "PLAN-063",
                    "docs/plans/PLAN-063-helix-db-detector-system.md#/W-7",
                    "carry",
                    "recurring carry",
                    "2026-05-12T00:00:00Z",
                ),
                (
                    "PLAN-063",
                    "docs/plans/PLAN-063-helix-db-detector-system.md#/W-7",
                    "carry",
                    "recurring carry",
                    "2026-05-12T01:00:00Z",
                ),
            ],
        )
    conn.commit()
finally:
    conn.close()
PY
}

run_gate() {
  local gate="$1"
  shift
  set +e
  run env HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_DISABLE_FEEDBACK=1 \
    "$HELIX_ROOT/cli/helix-gate" "$gate" --static-only --readiness-mode skip "$@"
  set -e
}

@test "G2 auto-runs axis-06/07/12 and fail-closes on failed detector" {
  seed_db_case "g2"

  run_gate "G2"
  [ "$status" -eq 1 ]
  [[ "$output" == *"[helix-gate] detector auto-run: G2"* ]]
  [[ "$output" == *"axis-06"* ]]
  [[ "$output" == *"=== G2 FAIL"* ]]
}

@test "G4 auto-runs axis-01/02/03/09/14 and fail-closes on failed detector" {
  seed_db_case "g4"

  run_gate "G4"
  [ "$status" -eq 1 ]
  [[ "$output" == *"[helix-gate] detector auto-run: G4"* ]]
  [[ "$output" == *"axis-01"* ]]
  [[ "$output" == *"=== G4 FAIL"* ]]
}

@test "G6 auto-runs axis-05/08/11 and fail-closes on failed detector" {
  seed_db_case "g6"

  run_gate "G6"
  [ "$status" -eq 1 ]
  [[ "$output" == *"[helix-gate] detector auto-run: G6"* ]]
  [[ "$output" == *"axis-05"* ]]
  [[ "$output" == *"=== G6 FAIL"* ]]
}
