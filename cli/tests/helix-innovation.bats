#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"

  TOOL_ROOT="$TMP_ROOT/tool"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$TOOL_ROOT" "$PROJECT_ROOT" "$HOME_DIR"
  cp -R "$HELIX_ROOT/cli" "$TOOL_ROOT/cli"

  export HELIX_HOME="$TOOL_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"

  git init -q "$PROJECT_ROOT"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "test_innovation_tech_dry_run_succeeds" {
  run "$TOOL_ROOT/cli/helix-innovation" tech --task "Stripe Engineering を日本向けに翻案"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[helix innovation] tech subagent prompt 生成完了"* ]]
  [[ "$output" == *'subagent_type: "pdm-tech-innovation"'* ]]
}

@test "test_innovation_marketing_dry_run_succeeds" {
  run "$TOOL_ROOT/cli/helix-innovation" marketing --task "PLG を国内 B2B SaaS に翻案"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[helix innovation] marketing subagent prompt 生成完了"* ]]
  [[ "$output" == *'subagent_type: "pdm-marketing-innovation"'* ]]
}

@test "test_innovation_synthesize_requires_input" {
  run "$TOOL_ROOT/cli/helix-innovation" synthesize --task "2 PdM 出力を統合"
  [ "$status" -eq 2 ]
  [[ "$output" == *"--tech-output は必須です"* ]]
}

@test "test_innovation_team_lists_members" {
  run "$TOOL_ROOT/cli/helix-innovation" team --task "新規プロダクト企画の方向性を整理"
  [ "$status" -eq 0 ]
  [[ "$output" == *"pdm-tech-innovation"* ]]
  [[ "$output" == *"pdm-marketing-innovation"* ]]
  [[ "$output" == *"pmo-tech-docs"* ]]
  [[ "$output" == *"pdm-innovation-manager"* ]]
}

@test "test_innovation_help_documents_options" {
  run "$TOOL_ROOT/cli/helix-innovation" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"tech --task"* ]]
  [[ "$output" == *"synthesize --task"* ]]
  [[ "$output" == *"--tech-output PATH"* ]]
  [[ "$output" == *"--marketing-output PATH"* ]]
}

@test "test_innovation_invalid_subcommand_errors" {
  run "$TOOL_ROOT/cli/helix-innovation" unknown
  [ "$status" -eq 2 ]
  [[ "$output" == *"不明なサブコマンドです: unknown"* ]]
}
