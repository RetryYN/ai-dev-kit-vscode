#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "docs role implementation skips review template" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --task "[タスク種別] 実装
README を更新してください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Task Type: 実装"* ]]
  [[ "$output" == *"Review Template: none"* ]]
  [[ "$output" == *"必ず apply_patch または Edit で実ファイル編集を実施する"* ]]
  [[ "$output" != *"HELIX レビュー prompt template"* ]]
}

@test "tl role implementation delegates instead of reviewing" {
  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "[タスク種別] 実装
CLI の仕様を更新してください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Task Type: 実装"* ]]
  [[ "$output" == *"Review Template: none"* ]]
  [[ "$output" == *'`delegate_to: <role>` / `blocked` / `route`'* ]]
  [[ "$output" != *"apply_patch / Edit OK"* ]]
  [[ "$output" != *"HELIX レビュー prompt template"* ]]
}

@test "docs role review includes review template" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --task "[タスク種別] レビュー
README をレビューしてください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Task Type: レビュー"* ]]
  [[ "$output" == *"Review Template: cli/templates/prompts/codex-review.md"* ]]
  [[ "$output" == *"HELIX レビュー prompt template"* ]]
}

@test "tl role review includes review template" {
  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "[タスク種別] レビュー
CLI をレビューしてください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Task Type: レビュー"* ]]
  [[ "$output" == *"Review Template: cli/templates/prompts/codex-review.md"* ]]
  [[ "$output" == *"HELIX レビュー prompt template"* ]]
}

@test "implementation verb is auto-inferred without review template" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --task "実装してください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Task Type: 実装"* ]]
  [[ "$output" == *"[タスク種別] 実装"* ]]
  [[ "$output" == *"Review Template: none"* ]]
}

@test "review verb is auto-inferred with review template" {
  run "$HELIX_ROOT/cli/helix-codex" --role docs --task "レビューしてください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Task Type: レビュー"* ]]
  [[ "$output" == *"[タスク種別] レビュー"* ]]
  [[ "$output" == *"Review Template: cli/templates/prompts/codex-review.md"* ]]
}
