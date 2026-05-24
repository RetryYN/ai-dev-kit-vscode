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

  git init -q
  git config user.email "incident@example.com"
  git config user.name "Incident Test"
  echo "# incident" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  "$HELIX_ROOT/cli/helix" init --project-name incident >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix incident help and top-level help include incident" {
  run "$HELIX_ROOT/cli/helix-incident" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"usage: helix incident"* ]]
  [[ "$output" == *"postmortem"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"incident"* ]]
}

@test "helix incident detect creates session" {
  run "$HELIX_ROOT/cli/helix" incident detect --incident-id INC-001 --summary "API outage" --severity P0 --env prod
  [ "$status" -eq 0 ]
  [[ "$output" == *"[HELIX Incident] INC-001 (detected)"* ]]
  [ -f "$PROJECT_ROOT/.helix/incident/CURRENT.json" ]
}

@test "helix incident triage and hotfix update active session" {
  "$HELIX_ROOT/cli/helix" incident detect --incident-id INC-002 --summary "latency spike" --severity P1 --env prod >/dev/null

  run "$HELIX_ROOT/cli/helix" incident triage --owner oncall --impact "checkout unavailable"
  [ "$status" -eq 0 ]
  [[ "$output" == *"(triaged)"* ]]
  [[ "$output" == *"kind=recovery"* ]]

  run "$HELIX_ROOT/cli/helix" incident hotfix --change "rollback deploy" --release-ref "deploy-123"
  [ "$status" -eq 0 ]
  [[ "$output" == *"(mitigated)"* ]]
}

@test "helix incident route prints forward formalization targets" {
  "$HELIX_ROOT/cli/helix" incident detect --incident-id INC-003 --summary "prod issue" --severity P1 --env prod >/dev/null
  "$HELIX_ROOT/cli/helix" incident triage --owner lead --impact "login degraded" >/dev/null
  "$HELIX_ROOT/cli/helix" incident hotfix --change "disable feature flag" >/dev/null

  run "$HELIX_ROOT/cli/helix" incident route
  [ "$status" -eq 0 ]
  [[ "$output" == *"L1:"* ]]
  [[ "$output" == *"L14:"* ]]
}

@test "helix incident postmortem writes markdown" {
  "$HELIX_ROOT/cli/helix" incident detect --incident-id INC-004 --summary "queue issue" --severity P1 --env prod >/dev/null
  "$HELIX_ROOT/cli/helix" incident triage --owner ops --impact "jobs delayed" >/dev/null
  "$HELIX_ROOT/cli/helix" incident hotfix --change "restart workers" >/dev/null

  run "$HELIX_ROOT/cli/helix" incident postmortem --output "$PROJECT_ROOT/docs/postmortem/INC-004.md"
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/docs/postmortem/INC-004.md" ]
}

@test "helix commands check passes after incident registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
