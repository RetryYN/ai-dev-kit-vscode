#!/usr/bin/env bats

source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  export HELIX_ROOT
  export BATS_TMP_ROOT_DIR="/tmp"
}

teardown() {
  rm -rf /tmp/bats-run-helix-cleanup-* /tmp/bats-test-helix-cleanup-* /tmp/tmp.foobar
}

@test "--list lists bats-run/test candidates with marker visibility" {
  mkdir -p /tmp/bats-run-helix-cleanup-foo
  mkdir -p /tmp/bats-test-helix-cleanup-bar
  helix_bats_mark /tmp/bats-run-helix-cleanup-foo

  run "$HELIX_ROOT/helix" bats-cleanup --list

  [ "$status" -eq 0 ]
  [[ "$output" == *"/tmp/bats-run-helix-cleanup-foo"* ]]
  [[ "$output" == *"/tmp/bats-test-helix-cleanup-bar"* ]]
  echo "$output" | grep -q '/tmp/bats-run-helix-cleanup-foo'
  echo "$output" | grep -q '/tmp/bats-test-helix-cleanup-bar'
  echo "$output" | grep -q 'marker='
}

@test "--dry-run shows delete candidates and does not delete" {
  mkdir -p /tmp/bats-test-helix-cleanup-dry
  helix_bats_mark /tmp/bats-test-helix-cleanup-dry

  run "$HELIX_ROOT/helix" bats-cleanup --dry-run --older-than 0

  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'delete target: /tmp/bats-test-helix-cleanup-dry'
  [ -d /tmp/bats-test-helix-cleanup-dry ]
}

@test "--delete removes marker-owned directories" {
  mkdir -p /tmp/bats-run-helix-cleanup-delete
  helix_bats_mark /tmp/bats-run-helix-cleanup-delete

  run "$HELIX_ROOT/helix" bats-cleanup --delete --older-than 0

  [ "$status" -eq 0 ]
  [[ "$output" == *"deleted_count=1"* ]]
  [[ "$output" == *"skip_count=0"* ]]
  [ ! -d /tmp/bats-run-helix-cleanup-delete ]
}

@test "--delete skips non-marked directories and keeps them" {
  mkdir -p /tmp/bats-test-helix-cleanup-nomark

  run "$HELIX_ROOT/helix" bats-cleanup --delete --older-than 0

  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'skip (no HELIX marker): /tmp/bats-test-helix-cleanup-nomark'
  [[ "$output" == *"deleted_count=0"* ]]
  [[ "$output" == *"skip_count=1"* ]]
  [ -d /tmp/bats-test-helix-cleanup-nomark ]
}

@test "/tmp/tmp.* is excluded from cleanup patterns" {
  mkdir -p /tmp/bats-run-helix-cleanup-keep
  mkdir -p /tmp/tmp.foobar

  run "$HELIX_ROOT/helix" bats-cleanup --list

  [ "$status" -eq 0 ]
  [[ "$output" == *"/tmp/bats-run-helix-cleanup-keep"* ]]
  [[ "$output" != *"/tmp/tmp.foobar"* ]]
}
