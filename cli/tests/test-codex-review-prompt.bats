#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

@test "helix-codex dry-run prepends common review template" {
  run "$HELIX_ROOT/cli/helix-codex" --role tl --task "レビューしてください" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"Review Template: cli/templates/codex-review-prompt.md"* ]]
  [[ "$output" == *"HELIX レビュー prompt template"* ]]
  [[ "$output" == *"overall_scores"* ]]
  [[ "$output" == *"dimension_scores"* ]]
}
