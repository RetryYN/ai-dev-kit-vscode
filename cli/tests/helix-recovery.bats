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
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$PROJECT_ROOT/docs/plans/L7"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "recovery@example.com"
  git config user.name "Recovery Test"
  echo "# recovery" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  "$HELIX_ROOT/cli/helix" init --project-name recovery >/dev/null

  cat > "$PROJECT_ROOT/docs/plans/L7/recovery-plan.md" <<'EOF'
---
plan_id: TEST-001
kind: recovery
status: draft
---

# Recovery Plan
EOF

  mkdir -p "$PROJECT_ROOT/cli/templates/plan/recovery"
  cat > "$PROJECT_ROOT/cli/templates/plan/recovery/postmortem-template.md" <<'EOF'
# Recovery Postmortem — {{PLAN_ID}}

{{RECOVERY_LOG}}
EOF
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix recovery help and top-level help include recovery" {
  run "$HELIX_ROOT/cli/helix-recovery" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage: helix recovery"* ]]
  [[ "$output" == *"postmortem"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"recovery"* ]]
}

@test "helix recovery start dry-run prints plan and phase" {
  run "$HELIX_ROOT/cli/helix" recovery start --plan-id TEST-001 --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"session 開始: TEST-001"* ]]
  [[ "$output" == *"[dry-run]"* ]]
  [[ "$output" == *"初期 Phase: RP-"* ]]
}

@test "helix recovery start creates session and status shows it" {
  run "$HELIX_ROOT/cli/helix" recovery start --plan-id TEST-001 --reopen-point L5
  [ "$status" -eq 0 ]
  [[ "$output" == *"CURRENT.json を初期化しました"* ]]

  run "$HELIX_ROOT/cli/helix" recovery status
  [ "$status" -eq 0 ]
  [[ "$output" == *"[HELIX Recovery] TEST-001 (active)"* ]]
  [[ "$output" == *"Forward 復帰先: L5"* ]]
}

@test "helix recovery phase show and advance work" {
  "$HELIX_ROOT/cli/helix" recovery start --plan-id TEST-001 >/dev/null

  run "$HELIX_ROOT/cli/helix" recovery phase --show
  [ "$status" -eq 0 ]
  [[ "$output" == RP-* ]]

  current_phase="$output"
  from_phase="${current_phase%% *}"
  run "$HELIX_ROOT/cli/helix" recovery phase --advance --from "$from_phase" --to RP-4
  [ "$status" -eq 0 ]
  [[ "$output" == *"RP-4"* ]]
}

@test "helix recovery log show and append work" {
  "$HELIX_ROOT/cli/helix" recovery start --plan-id TEST-001 >/dev/null

  run "$HELIX_ROOT/cli/helix" recovery log --append "契約差分を是正"
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" recovery log --show
  [ "$status" -eq 0 ]
  [[ "$output" == *"契約差分を是正"* ]]
}

@test "helix recovery postmortem writes markdown" {
  "$HELIX_ROOT/cli/helix" recovery start --plan-id TEST-001 >/dev/null

  run "$HELIX_ROOT/cli/helix" recovery postmortem --output "$PROJECT_ROOT/docs/postmortem/recovery.md"
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/docs/postmortem/recovery.md" ]
}

@test "helix recovery done dry-run passes with preflight ready" {
  "$HELIX_ROOT/cli/helix" recovery start --plan-id TEST-001 >/dev/null

  run "$HELIX_ROOT/cli/helix" recovery done --confirm-token PO-APPROVED-TEST-001 --skip-cutover --skip-reason "docs only"
  [ "$status" -eq 0 ]
  [[ "$output" == *"skipped"* ]]
}

@test "helix recovery status exits 1 when no session exists" {
  run "$HELIX_ROOT/cli/helix" recovery status
  [ "$status" -eq 1 ]
  [[ "$output" == *"No active recovery session"* ]]
}

@test "helix commands check passes after recovery registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
