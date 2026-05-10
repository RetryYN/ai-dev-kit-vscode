#!/usr/bin/env bats

@test "bats-lite: passing test reports ok" {
  [ 1 -eq 1 ]
}

@test "bats-lite: failing test reports not ok" {
  cat > /tmp/p051-fail.bats <<'BATS'
@test "intentional fail" {
  [ 1 -eq 0 ]
}
BATS

  run bats /tmp/p051-fail.bats
  [ "$status" -ne 0 ]
  echo "$output" | grep -q 'not ok'
  rm -f /tmp/p051-fail.bats
}

@test "bats-lite: skip reports ok with reason" {
  cat > /tmp/p051-skip.bats <<'BATS'
@test "skipped test" {
  skip "test reason"
}
BATS

  run bats /tmp/p051-skip.bats
  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'skipped: test reason'
  rm -f /tmp/p051-skip.bats
}

@test "bats-lite: errexit propagates inside test" {
  cat > /tmp/p051-errexit.bats <<'BATS'
@test "errexit" {
  false
  echo "after false (should NOT print)"
}
BATS

  run bats /tmp/p051-errexit.bats
  [ "$status" -ne 0 ]
  echo "$output" | grep -q 'not ok'
  ! echo "$output" | grep -q 'after false'
  rm -f /tmp/p051-errexit.bats
}
