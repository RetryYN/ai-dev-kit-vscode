#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TARGET="$HELIX_ROOT/cli/libexec/helix-session-start"
}

# DoD 検証: PLAN-084-integration-test-design.md adapter exclusion smoke
@test "helix-session-start keeps explicit legacy db writes and avoids compatibility_adapter" {
  adapter_count="$(grep -c "compatibility_adapter" "$TARGET" || true)"
  write_conn_count="$(grep -c "_write_connection" "$TARGET" || true)"

  [ "$adapter_count" -eq 0 ]
  [ "$write_conn_count" -ge 1 ]
}
