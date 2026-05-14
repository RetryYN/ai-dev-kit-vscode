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

seed_functional_freeze() {
  local drive="$1"
  shift

  python3 - "$HELIX_ROOT" "$PROJECT_ROOT" "$drive" "$@" <<'PY'
import sys
from pathlib import Path

helix_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
drive = sys.argv[3]
statuses = sys.argv[4:]
sys.path.insert(0, str(helix_root / "cli" / "lib"))

import helix_db

conn = helix_db.get_connection(project_root / ".helix" / "helix.db")
try:
    for idx, status in enumerate(statuses, start=1):
        conn.execute(
            """
            INSERT INTO design_sprint_entries (
                plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, freeze_gate, subgate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("PLAN-100", f"SPRINT-{idx}", "functional", "functional", drive, "shared", status, "G3", "functional_freeze"),
        )
    conn.commit()
finally:
    conn.close()
PY
}

write_phase_drive() {
  local drive="$1"
  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<YAML
current_phase: L3
sprint:
  drive: $drive
YAML
}

write_plan_frontmatter() {
  local drive="$1"
  mkdir -p "$PROJECT_ROOT/.helix/plans" "$PROJECT_ROOT/docs/plans"
  cat > "$PROJECT_ROOT/.helix/plans/PLAN-100.yaml" <<'YAML'
id: PLAN-100
title: "Sample Plan"
status: draft
created_at: "2026-05-15T00:00:00Z"
source_file: "docs/plans/PLAN-100-sample.md"
references: []
artifacts: []
finalized_at: null
review:
  status: approve
  reviewed_at: "2026-05-15T00:00:00Z"
  review_file: null
YAML
  cat > "$PROJECT_ROOT/docs/plans/PLAN-100-sample.md" <<YAML
---
plan_id: PLAN-100
title: Sample Plan
status: draft
created: 2026-05-15
drive: $drive
---

body
YAML
}

@test "test_subgate_functional_freeze_missing_data_returns_warning_for_be" {
  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100 --drive be
  [ "$status" -eq 0 ]
  [[ "$output" == *'"verdict": "missing"'* ]]
  [[ "$output" == *"WARN: functional_freeze missing (size=M, drive=be)"* ]]
}

@test "test_subgate_functional_freeze_missing_data_returns_fail_for_fe" {
  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100 --drive fe
  [ "$status" -eq 1 ]
  [[ "$output" == *'"verdict": "missing"'* ]]
  [[ "$output" == *"FAIL: functional_freeze missing (size=M, drive=fe)"* ]]
}

@test "test_subgate_functional_freeze_paired_passes" {
  write_phase_drive "be"
  seed_functional_freeze "fe" "paired"

  run env HELIX_SIZE=L "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100 --drive fe
  [ "$status" -eq 0 ]
  [[ "$output" == *'"verdict": "passed"'* ]]
  [[ "$output" == *'"paired_count": 1'* ]]
  [[ "$output" == *"auto-resolved=be, override=fe"* ]]
}

@test "test_subgate_functional_freeze_pending_fails" {
  seed_functional_freeze "fe" "pending"

  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100 --drive fe
  [ "$status" -eq 1 ]
  [[ "$output" == *'"verdict": "failed"'* ]]
  [[ "$output" == *"FAIL: functional_freeze failed (size=M, drive=fe)"* ]]
}

@test "test_subgate_requires_plan_id" {
  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --drive fe
  [ "$status" -eq 2 ]
  [[ "$output" == *"エラー: --subgate は --plan-id を必須"* ]]
}

@test "test_subgate_resolves_drive_from_phase_yaml" {
  write_phase_drive "fe"
  seed_functional_freeze "fe" "paired"

  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100
  [ "$status" -eq 0 ]
  [[ "$output" == *'"drive": "fe"'* ]]
}

@test "test_subgate_resolves_drive_from_plan_frontmatter" {
  write_plan_frontmatter "fullstack"
  seed_functional_freeze "fullstack" "paired"

  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100
  [ "$status" -eq 0 ]
  [[ "$output" == *'"drive": "fullstack"'* ]]
}

@test "test_subgate_requires_drive_only_when_auto_resolution_fails" {
  run "$HELIX_ROOT/cli/helix" gate G3 --subgate functional_freeze --plan-id PLAN-100
  [ "$status" -eq 1 ]
  [[ "$output" == *"エラー: functional_freeze の drive を解決できませんでした。--drive を指定してください"* ]]
}

@test "test_subgate_invalid_value_rejects" {
  run "$HELIX_ROOT/cli/helix" gate G3 --subgate nope --plan-id PLAN-100 --drive fe
  [ "$status" -eq 2 ]
  [[ "$output" == *"エラー: --subgate は functional_freeze のみサポート: nope"* ]]
}

@test "test_subgate_help_documents_options" {
  run "$HELIX_ROOT/cli/helix" gate --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"--subgate <name>"* ]]
  [[ "$output" == *"--drive <DRIVE>"* ]]
  [[ "$output" == *"現在 functional_freeze のみ"* ]]
}
