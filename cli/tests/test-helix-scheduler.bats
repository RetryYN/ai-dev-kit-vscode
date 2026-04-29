#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
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

@test "helix scheduler add/list/status/cancel" {
  run "$HELIX_ROOT/cli/helix" scheduler add --schedule "+5m" --task-type "helix:command" --task-payload "status" --id "bats-sched"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "bats-sched"'* ]]

  run "$HELIX_ROOT/cli/helix" scheduler list --status pending
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "bats-sched"'* ]]

  run "$HELIX_ROOT/cli/helix" scheduler status --id bats-sched
  [ "$status" -eq 0 ]
  [[ "$output" == *'"task_payload": "status"'* ]]

  run "$HELIX_ROOT/cli/helix" scheduler cancel --id bats-sched
  [ "$status" -eq 0 ]
  [[ "$output" == *'"cancelled": true'* ]]
}

@test "helix scheduler run-due dry-run reports due task without executing" {
  run "$HELIX_ROOT/cli/helix" scheduler add --schedule "+30s" --task-type "helix:command" --task-payload "status" --id "dry-run"
  [ "$status" -eq 0 ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("UPDATE schedules SET next_run_at = 1 WHERE id = 'dry-run'")
conn.commit()
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" scheduler run-due --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "dry-run"'* ]]
  [[ "$output" == *'"dry_run": true'* ]]
}
