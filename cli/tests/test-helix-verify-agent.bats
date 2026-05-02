#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix/patterns" "$PROJECT_ROOT/docs/plans" "$PROJECT_ROOT/docs/features/sample" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

write_plan() {
  cat > "$PROJECT_ROOT/docs/plans/PLAN-999-verify-agent-test.md" <<'MD'
# PLAN-999: verify agent test

## 検証
- pytest unit test を実行する
- security dependency validation を行う
MD
}

write_verify_tools() {
  cat > "$PROJECT_ROOT/.helix/patterns/verify-tools.yaml" <<'YAML'
version: 1
tools:
  - id: pytest
    category: unit-test
    languages: [py]
    license: MIT
    last_release_or_activity: 2026-03-20
    maintenance_signal: active
    official_source: https://pytest.org
    security_notes: []
    adoption_status: candidate_only
YAML
}

@test "helix verify-agent --help shows usage" {
  run "$HELIX_ROOT/cli/helix" verify-agent --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage: helix verify-agent"* ]]
  [[ "$output" == *"PLAN-010"* ]]
}

@test "helix verify-agent harvest --json returns candidates" {
  write_plan
  write_verify_tools

  run "$HELIX_ROOT/cli/helix" verify-agent harvest --plan docs/plans/PLAN-999-verify-agent-test.md --json

  [ "$status" -eq 0 ]
  printf '%s' "$output" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["subcommand"] == "harvest"; assert d["candidates"][0]["tool_id"] == "pytest"'
}

@test "helix verify-agent harvest fallback when verify-tools is missing" {
  write_plan

  run "$HELIX_ROOT/cli/helix" verify-agent harvest --plan docs/plans/PLAN-999-verify-agent-test.md --json

  [ "$status" -eq 0 ]
  printf '%s' "$output" | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d["candidates"][0]; assert c["source"] == "fallback"; assert c["adoption_status"] == "candidate_only"; assert "fallback_reason" in c'
}

@test "helix verify-agent design missing contract exits non-zero" {
  run "$HELIX_ROOT/cli/helix" verify-agent design --contract docs/features/sample/MISSING.md

  [ "$status" -ne 0 ]
  [[ "$output" == *"contract not found"* ]]
}

@test "helix verify-agent cross-check dry-run exits zero for identical plan" {
  write_plan

  run "$HELIX_ROOT/cli/helix" verify-agent cross-check --impl PLAN-999 --spec PLAN-999 --dry-run --json

  [ "$status" -eq 0 ]
  printf '%s' "$output" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["drifts"] == []; assert d["fail_close"] is False'
}

@test "helix verify-agent list is empty without v13 persistence" {
  run "$HELIX_ROOT/cli/helix" verify-agent list

  [ "$status" -eq 0 ]
  [[ "$output" == *"(empty)"* ]]
  [[ "$output" == *"v13"* ]]
}
