#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  printf "# recover test\n" > README.md
  git add README.md
  git commit -q -m "init"
  "$HELIX_ROOT/cli/helix" init --project-name recover >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix recover help and top-level help include recover" {
  run "$HELIX_ROOT/cli/helix-recover" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"helix recover <subcommand>"* ]]
  [[ "$output" == *"rollback"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"recover"* ]]
}

@test "helix recover check prints C1-C4 rows" {
  run "$HELIX_ROOT/cli/helix-recover" check
  [ "$status" -eq 0 ]
  [[ "$output" == *"[HELIX Recovery Check]"* ]]
  [[ "$output" == *"C1 大規模変更"* ]]
  [[ "$output" == *"C2 工程逸脱"* ]]
  [[ "$output" == *"C3 認識ズレ"* ]]
  [[ "$output" == *"C4 予算過剰"* ]]
}

@test "helix recover status reports empty state" {
  run "$HELIX_ROOT/cli/helix-recover" status
  [ "$status" -eq 0 ]
  [[ "$output" == *"No recovery logs found"* ]]
}

@test "helix recover dump writes recovery-log with required sections" {
  OUTPUT_PATH="$PROJECT_ROOT/.helix/recovery/test-recovery-log.md"
  run "$HELIX_ROOT/cli/helix-recover" dump --output "$OUTPUT_PATH"
  [ "$status" -eq 0 ]
  [ -f "$OUTPUT_PATH" ]
  run python3 -c "from cli.lib.recovery_plan_check import check_recovery_template_sections; assert check_recovery_template_sections('$OUTPUT_PATH') == []"
  [ "$status" -eq 0 ]
}

@test "helix recover rollback is dry-run only" {
  run "$HELIX_ROOT/cli/helix-recover" rollback --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"[dry-run]"* ]]

  run "$HELIX_ROOT/cli/helix-recover" rollback --apply
  [ "$status" -eq 2 ]
  [[ "$output" == *"use 'helix recover rollback --dry-run' first"* ]]
}

@test "helix commands check passes after recover registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
