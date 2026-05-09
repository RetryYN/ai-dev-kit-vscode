#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
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

@test "helix scheduler add-at accepts combined task and max dry-run" {
  run "$HELIX_ROOT/cli/helix" scheduler add-at --at "+5m" --task "helix:command:status" --id "at-run"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "at-run"'* ]]
  [[ "$output" == *'"schedule_expr": "at:+5m"'* ]]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("UPDATE schedules SET next_run_at = 1 WHERE id = 'at-run'")
conn.commit()
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" scheduler run-due --dry-run --max 1
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "at-run"'* ]]
}

@test "helix scheduler requeue-stale recovers stuck running schedules" {
  run "$HELIX_ROOT/cli/helix" scheduler add --schedule "+30s" --task "helix:command:status" --id "stale-sched"
  [ "$status" -eq 0 ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("UPDATE schedules SET status = 'running', updated_at = 1 WHERE id = 'stale-sched'")
conn.commit()
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" scheduler requeue-stale --older-than 60
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "stale-sched"'* ]]
  [[ "$output" == *'"stale_action": "requeued"'* ]]

  run "$HELIX_ROOT/cli/helix" scheduler status --id stale-sched
  [ "$status" -eq 0 ]
  [[ "$output" == *'"status": "pending"'* ]]
}
