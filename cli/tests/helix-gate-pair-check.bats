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

seed_review_pair() {
  local layer="$1"
  local vertical="$2"
  local horizontal="$3"

  python3 - "$HELIX_ROOT" "$PROJECT_ROOT" "$layer" "$vertical" "$horizontal" <<'PY'
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
layer = sys.argv[3]
vertical = sys.argv[4] == "true"
horizontal = sys.argv[5] == "true"
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import helix_db

conn = helix_db.get_connection(project_root / ".helix" / "helix.db")
try:
    if vertical:
        conn.execute(
            """
            INSERT INTO design_review (
                plan_id, layer, review_axis, source_layer, target_id, reviewed_at, reviewer, verdict, raw_findings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("PLAN-063", layer, "vertical", "source-layer", 1, "2026-05-13T00:00:00Z", "codex", "passed", ""),
        )
    if horizontal:
        conn.execute(
            """
            INSERT INTO design_review (
                plan_id, layer, review_axis, source_layer, target_id, reviewed_at, reviewer, verdict, raw_findings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("PLAN-063", layer, "horizontal", "source-layer", 1, "2026-05-13T00:00:00Z", "codex", "passed", ""),
        )
    conn.commit()
finally:
    conn.close()
PY
}

@test "helix gate G2 --pair-check architecture --plan-id PLAN-063 passes when both axes passed" {
  seed_review_pair "architecture" "true" "true"

  run "$HELIX_ROOT/cli/helix" gate G2 --pair-check architecture --plan-id PLAN-063
  [ "$status" -eq 0 ]
  [[ "$output" == *"[pair-check] gate=G2 plan_id=PLAN-063 layer=architecture vertical_passed=True horizontal_passed=True"* ]]
}

@test "helix gate G2 --pair-check architecture --plan-id PLAN-063 fails when only vertical passed" {
  seed_review_pair "architecture" "true" "false"

  run "$HELIX_ROOT/cli/helix" gate G2 --pair-check architecture --plan-id PLAN-063
  [ "$status" -eq 1 ]
  [[ "$output" == *"G2 fail: design_review pair missing"* ]]
  [[ "$output" == *"vertical_passed=True"* ]]
  [[ "$output" == *"horizontal_passed=False"* ]]
}

@test "helix gate G2 --pair-check architecture --plan-id PLAN-063 fails when pair is missing" {
  run "$HELIX_ROOT/cli/helix" gate G2 --pair-check architecture --plan-id PLAN-063
  [ "$status" -eq 1 ]
  [[ "$output" == *"G2 fail: design_review pair missing"* ]]
  [[ "$output" == *"vertical_passed=False"* ]]
  [[ "$output" == *"horizontal_passed=False"* ]]
}

@test "helix gate G2 --pair-check invalid_layer exits 2" {
  run "$HELIX_ROOT/cli/helix" gate G2 --pair-check invalid_layer --plan-id PLAN-063
  [ "$status" -eq 2 ]
  [[ "$output" == *"エラー: --pair-check には requirement|architecture|detailed|functional|planning を指定してください"* ]]
}
