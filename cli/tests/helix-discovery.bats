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
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

assert_alias_equivalence() {
  local subcmd="$1"
  shift

  run helix discovery "$subcmd" "$@"
  [ "$status" -eq 0 ]
  local discovery_out="$output"

  stdout_file="$TMP_ROOT/${subcmd}.stdout"
  stderr_file="$TMP_ROOT/${subcmd}.stderr"
  HELIX_SUPPRESS_LEGACY_WARN="" helix scrum "$subcmd" "$@" >"$stdout_file" 2>"$stderr_file"
  [ "$?" -eq 0 ]
  alias_out="$(cat "$stdout_file")"
  alias_err="$(cat "$stderr_file")"
  [ "$alias_out" = "$discovery_out" ]
  [[ "$alias_err" == *"DEPRECATED"* ]]
  [[ "$alias_out" != *"DEPRECATED"* ]]

  HELIX_SUPPRESS_LEGACY_WARN=1 helix scrum "$subcmd" "$@" >"$stdout_file" 2>"$stderr_file"
  [ "$?" -eq 0 ]
  alias_out="$(cat "$stdout_file")"
  alias_err="$(cat "$stderr_file")"
  [ "$alias_out" = "$discovery_out" ]
  [[ "$alias_err" != *"DEPRECATED"* ]]
}

@test "helix discovery routes all documented subcommands" {
  for subcmd in init backlog local plan poc verify decide review status trigger web-search acceptance-design; do
    run helix discovery "$subcmd" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"helix discovery"* || "$output" == *"HELIX Discovery"* ]]
  done
}

@test "helix scrum alias matches discovery help outputs" {
  for subcmd in init backlog local plan poc verify decide review status trigger web-search acceptance-design; do
    assert_alias_equivalence "$subcmd" --help
  done
}

@test "helix router exposes discovery and keeps scrum alias" {
  run helix help
  [ "$status" -eq 0 ]
  [[ "$output" == *"discovery"* ]]
  [[ "$output" == *"scrum"* ]]
}
