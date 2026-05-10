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

@test "test_block_repo_python_edit" {
  run run_hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$HELIX_ROOT/cli/lib/budget.py\"}}"
  [ "$status" -eq 2 ]
  [[ "$output" == *"block"* ]]
}

@test "test_block_repo_docs_edit" {
  run run_hook "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$HELIX_ROOT/docs/architecture/x.md\"}}"
  [ "$status" -eq 2 ]
}

@test "test_allow_memory_dir" {
  memory_file="$HOME_DIR/.claude/projects/demo/memory/x.md"
  mkdir -p "$(dirname "$memory_file")"
  run run_hook "{\"tool_name\":\"MultiEdit\",\"tool_input\":{\"file_path\":\"$memory_file\"}}"
  [ "$status" -eq 0 ]
}

@test "test_allow_plan_md_with_env" {
  mkdir -p docs/plans
  touch docs/plans/PLAN-NNN-x.md
  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"docs/plans/PLAN-NNN-x.md"}}' HELIX_ALLOW_OPUS_PLAN_FIX=1
  [ "$status" -eq 0 ]
}

@test "test_escape_hatch" {
  run run_hook '{"tool_name":"Edit","tool_input":{"file_path":"cli/x.py"}}' HELIX_ALLOW_OPUS_REPO_EDIT=1 HELIX_OPUS_EDIT_REASON='emergency fix'
  [ "$status" -eq 0 ]
}
