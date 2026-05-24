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
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "9mode-e2e@example.com"
  git config user.name "9 Mode E2E Test"
  printf "# 9 mode e2e\n" > README.md
  git add README.md
  git commit -q -m "init"

  "$HELIX_ROOT/cli/helix" init --project-name 9mode-e2e >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

assert_help_output() {
  [ "$status" -eq 0 ]
  [ -n "$output" ]
  [[ "$output" == *"$1"* ]]
}

function forward_mode_startup_help_and_drive_sanity_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "mode"
  [[ "$output" == *"Forward"* ]]

  run "$HELIX_ROOT/cli/helix" mode --help
  assert_help_output "forward"

  run "$HELIX_ROOT/cli/helix" mode --drive be --dry-run
  assert_help_output "Drive 切替プレビュー"
}

function reverse_mode_startup_help_and_r0_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "reverse"

  run "$HELIX_ROOT/cli/helix" reverse --help
  assert_help_output "Types:"

  run "$HELIX_ROOT/cli/helix" reverse code R0 --help
  assert_help_output "helix reverse code R0"
}

function discovery_mode_startup_help_and_init_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "discovery"

  run "$HELIX_ROOT/cli/helix" discovery --help
  assert_help_output "helix discovery"

  run "$HELIX_ROOT/cli/helix" discovery init --help
  assert_help_output "Usage: helix discovery init"
}

function refactor_mode_startup_help_and_init_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "refactor"

  run "$HELIX_ROOT/cli/helix" refactor --help
  assert_help_output "helix refactor"

  run "$HELIX_ROOT/cli/helix" refactor init --help
  assert_help_output "helix refactor init"
}

function retrofit_mode_startup_help_and_init_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "retrofit"

  run "$HELIX_ROOT/cli/helix" retrofit --help
  assert_help_output "helix retrofit"

  run "$HELIX_ROOT/cli/helix" retrofit init --help
  assert_help_output "helix retrofit"
  [[ "$output" == *"init"* ]]
}

function recovery_mode_startup_help_and_start_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "recovery"

  run "$HELIX_ROOT/cli/helix" recovery help
  assert_help_output "helix recovery"

  run "$HELIX_ROOT/cli/helix" recovery start --help
  assert_help_output "helix recovery start"
}

function scrum_agile_mode_startup_help_and_init_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "scrum-agile"

  run "$HELIX_ROOT/cli/helix" scrum-agile --help
  assert_help_output "helix scrum-agile"

  run "$HELIX_ROOT/cli/helix" scrum-agile init --help
  assert_help_output "helix scrum-agile init"
}

function incident_mode_startup_help_and_detect_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "incident"

  run "$HELIX_ROOT/cli/helix" incident --help
  assert_help_output "helix incident"

  run "$HELIX_ROOT/cli/helix" incident detect --help
  assert_help_output "helix incident detect"
}

function add_feature_mode_startup_help_and_add_design_help_work_through_router { #@test
  run "$HELIX_ROOT/cli/helix" help
  assert_help_output "add-feature"

  run "$HELIX_ROOT/cli/helix" add-feature --help
  assert_help_output "helix add-feature"

  run "$HELIX_ROOT/cli/helix" add-feature add-design --help
  assert_help_output "helix add-feature add-design"
}
