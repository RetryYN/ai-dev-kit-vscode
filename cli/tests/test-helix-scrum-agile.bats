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

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "scrum-agile@example.com"
  git config user.name "Scrum Agile Test"
  printf "# scrum agile\n" > README.md
  git add README.md
  git commit -q -m "init"

  "$HELIX_ROOT/cli/helix" init --project-name scrum-agile >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix scrum-agile help and top-level help include scrum-agile" {
  run "$HELIX_ROOT/cli/helix-scrum-agile" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"helix scrum-agile"* ]]
  [[ "$output" == *"increment"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"scrum-agile"* ]]
}

@test "helix scrum-agile init creates state files" {
  run "$HELIX_ROOT/cli/helix" scrum-agile init
  [ "$status" -eq 0 ]
  [[ "$output" == *".helix/scrum-agile"* ]]
  [ -f "$PROJECT_ROOT/.helix/scrum-agile/backlog.yaml" ]
  [ -f "$PROJECT_ROOT/.helix/scrum-agile/sprint.yaml" ]
}

@test "helix scrum-agile backlog add and plan create active sprint" {
  "$HELIX_ROOT/cli/helix" scrum-agile init >/dev/null

  run "$HELIX_ROOT/cli/helix" scrum-agile backlog add \
    --title "認証導線を合わせる" \
    --description "ユーザーと要件を詰める" \
    --priority high
  [ "$status" -eq 0 ]
  [[ "$output" == *"SB-001"* ]]

  run "$HELIX_ROOT/cli/helix" scrum-agile plan --goal "認証導線の合意" --item SB-001
  [ "$status" -eq 0 ]
  [[ "$output" == *"SPRINT-001"* ]]
  [[ "$output" == *"認証導線の合意"* ]]
}

@test "helix scrum-agile review retro increment completes sprint and prints reverse guidance" {
  "$HELIX_ROOT/cli/helix" scrum-agile init >/dev/null
  "$HELIX_ROOT/cli/helix" scrum-agile backlog add \
    --title "契約差分を詰める" \
    --description "review 用の叩き台を整理" >/dev/null
  "$HELIX_ROOT/cli/helix" scrum-agile plan --goal "契約差分の整理" --item SB-001 >/dev/null

  run "$HELIX_ROOT/cli/helix" scrum-agile review --summary "方向性を確認" --feedback "このまま進める"
  [ "$status" -eq 0 ]
  [[ "$output" == *"review recorded"* ]]

  run "$HELIX_ROOT/cli/helix" scrum-agile retro \
    --went-well "早く確認できた" \
    --improve "説明不足" \
    --action "DoD を先に共有する"
  [ "$status" -eq 0 ]
  [[ "$output" == *"retro recorded"* ]]

  run "$HELIX_ROOT/cli/helix" scrum-agile increment --title "契約差分 increment" --summary "実装可能な粒度まで整理"
  [ "$status" -eq 0 ]
  [[ "$output" == *"reverse_fullback_ready: true"* ]]
  [[ "$output" == *"helix reverse fullback"* ]]
}

@test "helix commands check passes after scrum-agile registration" {
  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
