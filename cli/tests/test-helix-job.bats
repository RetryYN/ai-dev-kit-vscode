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

@test "helix job enqueue status cancel retry smoke" {
  run "$HELIX_ROOT/cli/helix" job enqueue --task-type "helix:command" --task-payload "status" --id "bats-job"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "bats-job"'* ]]

  run "$HELIX_ROOT/cli/helix" job status --id bats-job
  [ "$status" -eq 0 ]
  [[ "$output" == *'"task_payload": "status"'* ]]

  run "$HELIX_ROOT/cli/helix" job cancel --id bats-job
  [ "$status" -eq 0 ]
  [[ "$output" == *'"cancelled": true'* ]]

  run "$HELIX_ROOT/cli/helix" job enqueue --task-type "shell:script" --task-payload "$TMP_ROOT/not-allowlisted.sh" --id "failed-job" --max-retries 0
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" job worker --max-jobs 1 --idle-sleep 0
  [ "$status" -eq 0 ]
  [[ "$output" == *'"status": "failed"'* ]]

  run "$HELIX_ROOT/cli/helix" job retry --id failed-job
  [ "$status" -eq 0 ]
  [[ "$output" == *'"retried": true'* ]]

  run "$HELIX_ROOT/cli/helix" job status --id failed-job
  [ "$status" -eq 0 ]
  [[ "$output" == *'"status": "pending"'* ]]
}

@test "helix job worker runs one allowlisted shell job" {
  SCRIPT="$TMP_ROOT/allowed.sh"
  MARKER="$TMP_ROOT/ran.txt"
  mkdir -p "$HOME_DIR/.config/helix"
  printf '#!/bin/sh\necho ran > %s\n' "$MARKER" > "$SCRIPT"
  chmod +x "$SCRIPT"
  printf 'shell_scripts:\n  - %s\n' "$SCRIPT" > "$HOME_DIR/.config/helix/automation-allowlist.yaml"

  run "$HELIX_ROOT/cli/helix" job enqueue --task-type "shell:script" --task-payload "$SCRIPT" --id "worker-job"
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" job worker --max-jobs 1 --idle-sleep 0
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "worker-job"'* ]]
  [[ "$output" == *'"status": "success"'* ]]
  [ "$(cat "$MARKER")" = "ran" ]
}

@test "helix job list accepts combined task enqueue" {
  run "$HELIX_ROOT/cli/helix" job enqueue --task "helix:command:status" --id "list-job"
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" job list --status pending --limit 1
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "list-job"'* ]]
}

@test "helix job requeue-stale recovers stuck running jobs" {
  run "$HELIX_ROOT/cli/helix" job enqueue --task "helix:command:status" --id "stale-job"
  [ "$status" -eq 0 ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("UPDATE jobs SET status = 'running', started_at = 1 WHERE id = 'stale-job'")
conn.commit()
PY
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" job requeue-stale --older-than 60
  [ "$status" -eq 0 ]
  [[ "$output" == *'"id": "stale-job"'* ]]
  [[ "$output" == *'"stale_action": "requeued"'* ]]

  run "$HELIX_ROOT/cli/helix" job status --id stale-job
  [ "$status" -eq 0 ]
  [[ "$output" == *'"status": "pending"'* ]]
}
