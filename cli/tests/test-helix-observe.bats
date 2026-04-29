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

@test "helix observe log records redacted event" {
  run "$HELIX_ROOT/cli/helix" observe log --event bats_event --data '{"password":"secret","key":"val"}'
  [ "$status" -eq 0 ]
  [[ "$output" == *"recorded event id="* ]]

  run python3 -c 'import json, sqlite3, sys; conn = sqlite3.connect(sys.argv[1]); row = conn.execute("SELECT data_json FROM events WHERE event_name = ?", ("bats_event",)).fetchone(); data = json.loads(row[0]); raise SystemExit(0 if data == {"password": "***", "key": "val"} else 1)' "$PROJECT_ROOT/.helix/helix.db"
  [ "$status" -eq 0 ]
}

@test "helix observe metric and report returns metric" {
  run "$HELIX_ROOT/cli/helix" observe metric --name latency --value 12.3 --tags "env=prod"
  [ "$status" -eq 0 ]
  [[ "$output" == *"recorded metric id="* ]]

  run "$HELIX_ROOT/cli/helix" observe report --metric latency --since "2026-01-01"
  [ "$status" -eq 0 ]
  [[ "$output" == *"metric latency value=12.3"* ]]
  [[ "$output" == *'"env": "prod"'* ]]
}
