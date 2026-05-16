#!/usr/bin/env bats

setup() {
  TOOL_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  PROJECT_ROOT="$(mktemp -d)"
  mkdir -p "$PROJECT_ROOT/.helix"
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: test-project
current_mode: forward
current_phase: L4
gates: {}
sprint:
  current_step: null
  status: active
  drive: be
  tracks: null
  phase: null
  phase_b: { current_step: null, status: pending, steps: { .b1: { status: pending } } }
  steps: { .1a: { status: pending }, .2: { status: pending } }
  ui: false
reverse_gates: {}
YAML
  python3 - "$PROJECT_ROOT/.helix/helix.db" <<PY
import sys
sys.path.insert(0, "${TOOL_ROOT}/cli/lib")
import helix_db
db = sys.argv[1]
with helix_db._write_connection(db) as conn:
    helix_db.migrate(conn)
PY
}

teardown() {
  rm -rf "$PROJECT_ROOT"
}

@test "helix-push --gate records automation_run row" {
  run env HELIX_HOME="$TOOL_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_DB_PATH="$PROJECT_ROOT/.helix/helix.db" "$TOOL_ROOT/cli/helix-push" --gate
  [ "$status" -eq 0 ] || [ "$status" -eq 1 ]

  row="$(sqlite3 "$PROJECT_ROOT/.helix/helix.db" "SELECT run_kind, status FROM automation_runs ORDER BY id LIMIT 1")"
  [[ "$row" == "push|completed" ]] || [[ "$row" == "push|failed" ]]
}
