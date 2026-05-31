#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"
  echo init > README.md
  git add README.md
  git commit -q -m "init"
  export HOME="$HOME_DIR"
  export HELIX_ROOT
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_hook() {
  local payload="$1"
  shift
  env "$@" "$HELIX_ROOT/.claude/hooks/pretooluse-opus-repo-block.sh" <<<"$payload"
}

@test "test_allow_master_repo_edit_when_project_root_matches_fallback_master" {
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$HELIX_ROOT/cli/lib/budget.py\"}}" CLAUDE_PROJECT_DIR="$HELIX_ROOT"
  [ "$status" -eq 0 ]
}

@test "test_allow_master_repo_edit_when_project_root_matches_home_core_master" {
  mkdir -p "$HOME_DIR/.helix"
  ln -s "$PROJECT_ROOT" "$HOME_DIR/.helix/core"
  consumer_file="$PROJECT_ROOT/cli/lib/budget.py"
  mkdir -p "$(dirname "$consumer_file")"
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$consumer_file\"}}" CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
  [ "$status" -eq 0 ]
}

@test "test_block_consumer_repo_edit" {
  consumer_file="$PROJECT_ROOT/cli/lib/budget.py"
  mkdir -p "$(dirname "$consumer_file")"
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$consumer_file\"}}" CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
  [ "$status" -eq 2 ]
  [[ "$output" == *"blocked"* ]]
}

@test "test_allow_consumer_project_helix_dir" {
  state_file="$PROJECT_ROOT/.helix/state/current.json"
  mkdir -p "$(dirname "$state_file")"
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$state_file\"}}" CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
  [ "$status" -eq 0 ]
}

@test "test_allow_memory_dir_consumer" {
  memory_file="$HOME_DIR/.claude/projects/demo/memory/x.md"
  mkdir -p "$(dirname "$memory_file")"
  run run_hook "{\"tool_name\":\"MultiEdit\",\"tool_input\":{\"file_path\":\"$memory_file\"}}" CLAUDE_PROJECT_DIR="$PROJECT_ROOT"
  [ "$status" -eq 0 ]
}

@test "test_allow_plan_md_with_env_consumer" {
  plan_file="$PROJECT_ROOT/docs/plans/PLAN-NNN-x.md"
  mkdir -p "$(dirname "$plan_file")"
  touch "$plan_file"
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$plan_file\"}}" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" HELIX_ALLOW_OPUS_PLAN_FIX=1
  [ "$status" -eq 0 ]
}

@test "test_escape_hatch_consumer" {
  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"cli/x.py"}}' CLAUDE_PROJECT_DIR="$PROJECT_ROOT" HELIX_ALLOW_OPUS_REPO_EDIT=1 HELIX_OPUS_EDIT_REASON='emergency fix'
  [ "$status" -eq 0 ]
}

@test "test_suppress_hook_consumer" {
  consumer_file="$PROJECT_ROOT/cli/lib/budget.py"
  mkdir -p "$(dirname "$consumer_file")"
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$consumer_file\"}}" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" HELIX_SUPPRESS_HOOK=1
  [ "$status" -eq 0 ]
}
