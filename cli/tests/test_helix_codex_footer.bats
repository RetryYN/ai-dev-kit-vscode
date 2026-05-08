#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$HELIX_ROOT/cli:$PATH"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix-codex dry-run appends common footer after TASK_INPUT_END" {
  run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer test" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *$'---TASK_INPUT_END---\n\n## 出力フォーマット (helix-codex 自動付加、上書き禁止)'* ]]
}

@test "HELIX_CODEX_NO_FOOTER disables the common footer" {
  HELIX_CODEX_NO_FOOTER=1 run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer off" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" != *"出力フォーマット (helix-codex 自動付加、上書き禁止)"* ]]
}

@test "helix-codex footer includes summary decision and tail guidance" {
  run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer contents" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"summary は 5 行以内で末尾に置く"* ]]
  [[ "$output" == *"decision (passed/failed/blocked/changes_required)"* ]]
  [[ "$output" == *"tail -30"* ]]
}

@test "helix-codex dry-run shows both discipline prompt and output footer" {
  run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer coexist" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"## Codex Mandatory Discipline"* ]]
  [[ "$output" == *"No Commit (委譲 Codex 限定ルール)"* ]]
  [[ "$output" == *"## 出力フォーマット (helix-codex 自動付加、上書き禁止)"* ]]
}
