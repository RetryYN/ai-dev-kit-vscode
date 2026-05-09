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
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix scrum web-search と acceptance-design は help を表示できる" {
  run "$HELIX_ROOT/cli/helix-scrum" web-search --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage: helix scrum web-search"* ]]

  run "$HELIX_ROOT/cli/helix-scrum" acceptance-design --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage: helix scrum acceptance-design"* ]]
}

@test "helix scrum web-search は reference を保存し acceptance-design はテンプレを出力する" {
  run "$HELIX_ROOT/cli/helix-scrum" init
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-scrum" backlog add --id H001 --title "検索仮説" --question "事例が見つかるか" --acceptance "1件以上の参考事例を保存できる"
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix-scrum" web-search --query "test" --hypothesis H001
  [ "$status" -eq 0 ]
  [[ "$output" == *"web-search saved"* ]]

  research_count="$(find "$PROJECT_ROOT/.helix/scrum/research/H001" -type f -name '*.md' | wc -l | tr -d ' ')"
  [ "$research_count" -ge 1 ]
  grep -R "Reference URL:" "$PROJECT_ROOT/.helix/scrum/research/H001" >/dev/null
  grep -R "Summary:" "$PROJECT_ROOT/.helix/scrum/research/H001" >/dev/null

  run "$HELIX_ROOT/cli/helix-scrum" acceptance-design --hypothesis H001
  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/.helix/scrum/acceptance/H001.md" ]
  grep -q "PoC Acceptance Criteria" "$PROJECT_ROOT/.helix/scrum/acceptance/H001.md"
}
