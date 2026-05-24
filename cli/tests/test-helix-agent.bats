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
  git config user.email "agent@example.com"
  git config user.name "Agent Test"
  echo "# agent" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  "$HELIX_ROOT/cli/helix" init --project-name agent >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix agent help lists HELIX W subcommands" {
  run "$HELIX_ROOT/cli/helix-agent" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"init"* ]]
  [[ "$output" == *"stage1"* ]]
  [[ "$output" == *"stage2"* ]]
  [[ "$output" == *"merge"* ]]
  [[ "$output" == *"route"* ]]
}

@test "helix agent init creates current session" {
  run "$HELIX_ROOT/cli/helix" agent init --agent-id AG-101 --summary "agent kickoff"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[HELIX Agent] AG-101 (initialized)"* ]]
  [ -f "$PROJECT_ROOT/.helix/agent/CURRENT.json" ]
}

@test "helix agent stage1 and stage2 then route shows phase2 then phase3" {
  "$HELIX_ROOT/cli/helix" agent init --agent-id AG-102 --summary "two-stage" >/dev/null

  run "$HELIX_ROOT/cli/helix" agent stage1 --plan-id L7-phase1-plan --drive fullstack --status ready
  [ "$status" -eq 0 ]
  [[ "$output" == *"(phase1_ready)"* ]]

  run "$HELIX_ROOT/cli/helix" agent route
  [ "$status" -eq 0 ]
  [[ "$output" == *"phase: phase2"* ]]
  [[ "$output" == *"drive: agent"* ]]

  run "$HELIX_ROOT/cli/helix" agent stage2 --plan-id L7-phase2-plan --status ready
  [ "$status" -eq 0 ]
  [[ "$output" == *"(phase2_ready)"* ]]

  run "$HELIX_ROOT/cli/helix" agent merge --plan-id L10-phase3-plan
  [ "$status" -eq 0 ]
  [[ "$output" == *"(phase3_ready)"* ]]

  run "$HELIX_ROOT/cli/helix" agent route
  [ "$status" -eq 0 ]
  [[ "$output" == *"phase: phase3"* ]]
  [[ "$output" == *"L10, L11, L12, L13, L14"* ]]
}

@test "helix agent merge fails before stage2 ready" {
  "$HELIX_ROOT/cli/helix" agent init --agent-id AG-103 --summary "blocked merge" >/dev/null
  "$HELIX_ROOT/cli/helix" agent stage1 --plan-id L7-phase1-plan --drive be --status ready >/dev/null

  run "$HELIX_ROOT/cli/helix" agent merge --plan-id L10-phase3-plan
  [ "$status" -ne 0 ]
  [[ "$output" == *"stage2"* ]]
}
