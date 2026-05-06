#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"

  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "helix@example.test"
  git config user.name "HELIX Test"
  touch README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

entry_add_foo() {
  "$HELIX_ROOT/cli/helix" entry add --id=foo.bar --axis=test --ref=tests/foo.py --lifecycle=initial
}

@test "helix entry --help displays usage" {
  run "$HELIX_ROOT/cli/helix" entry --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"show"* ]]
  [[ "$output" == *"list"* ]]
  [[ "$output" == *"add"* ]]
  [[ "$output" == *"update"* ]]
  [[ "$output" == *"link"* ]]
}

@test "helix entry list is empty after init" {
  run "$HELIX_ROOT/cli/helix" entry list
  [ "$status" -eq 0 ]
  [ -z "$output" ]

  run "$HELIX_ROOT/cli/helix" entry list --json
  [ "$status" -eq 0 ]
  [[ "$output" == *'"entries": []'* ]]
}

@test "helix entry add creates entry" {
  run "$HELIX_ROOT/cli/helix" entry add --id=foo.bar --axis=test --ref=tests/foo.py --lifecycle=initial
  [ "$status" -eq 0 ]
}

@test "helix entry show displays added entry" {
  entry_add_foo

  run "$HELIX_ROOT/cli/helix" entry show foo.bar
  [ "$status" -eq 0 ]
  [[ "$output" == *"axis: test"* ]]
}

@test "helix entry show missing exits 2" {
  run "$HELIX_ROOT/cli/helix" entry show nonexistent
  [ "$status" -eq 2 ]
}

@test "helix entry add without axis exits 64" {
  run "$HELIX_ROOT/cli/helix" entry add --id=missing.axis --ref=r --lifecycle=initial
  [ "$status" -eq 64 ]
}

@test "helix entry add duplicate id exits 64" {
  "$HELIX_ROOT/cli/helix" entry add --id=duplicate --axis=test --ref=r --lifecycle=initial

  run "$HELIX_ROOT/cli/helix" entry add --id=duplicate --axis=test --ref=r --lifecycle=initial
  [ "$status" -eq 64 ]
}

@test "helix entry update changes lifecycle" {
  entry_add_foo

  run "$HELIX_ROOT/cli/helix" entry update foo.bar --lifecycle=modification
  [ "$status" -eq 0 ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
value = conn.execute("SELECT lifecycle FROM entries WHERE id = 'foo.bar'").fetchone()[0]
raise SystemExit(0 if value == "modification" else 1)
PY
  [ "$status" -eq 0 ]
}

@test "helix entry link creates coverage link" {
  entry_add_foo
  "$HELIX_ROOT/cli/helix" entry add --id=cov.entry --axis=code --ref=src/c.py --lifecycle=initial

  run "$HELIX_ROOT/cli/helix" entry link foo.bar cov.entry --kind=covers
  [ "$status" -eq 0 ]
}

@test "helix entry unlink deletes coverage link" {
  entry_add_foo
  "$HELIX_ROOT/cli/helix" entry add --id=cov.entry --axis=code --ref=src/c.py --lifecycle=initial
  "$HELIX_ROOT/cli/helix" entry link foo.bar cov.entry --kind=covers

  run "$HELIX_ROOT/cli/helix" entry unlink foo.bar cov.entry --kind=covers
  [ "$status" -eq 0 ]

  run python3 - "$PROJECT_ROOT/.helix/helix.db" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
count = conn.execute(
    "SELECT COUNT(*) FROM links WHERE from_id = 'foo.bar' AND to_id = 'cov.entry' AND kind = 'covers'"
).fetchone()[0]
raise SystemExit(0 if count == 0 else 1)
PY
  [ "$status" -eq 0 ]
}

@test "helix entry coverage triplet json is parseable" {
  entry_add_foo

  run "$HELIX_ROOT/cli/helix" entry coverage --triplet --json
  [ "$status" -eq 0 ]
  run python3 - <<'PY' <<<"$output"
import json
import sys

payload = json.load(sys.stdin)
assert "triplet" in payload
assert isinstance(payload["triplet"], list)
PY
  [ "$status" -eq 0 ]
}

@test "helix entry list filters by axis" {
  entry_add_foo
  "$HELIX_ROOT/cli/helix" entry add --id=code.entry --axis=code --ref=src/c.py --lifecycle=initial

  run "$HELIX_ROOT/cli/helix" entry list --axis=test
  [ "$status" -eq 0 ]
  [[ "$output" == *"foo.bar"* ]]
  [[ "$output" != *"code.entry"* ]]
}
