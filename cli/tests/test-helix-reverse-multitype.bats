#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PATH="$HELIX_ROOT/cli:$PATH"
  export HELIX_DISABLE_FEEDBACK=1

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cp "$HELIX_ROOT/cli/templates/phase.yaml" "$PROJECT_ROOT/.helix/phase.yaml"
  cd "$PROJECT_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix reverse code --help shows code overview" {
  run "$HELIX_ROOT/cli/helix" reverse code --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"code"* ]]
  [[ "$output" == *"Existing Reverse HELIX behavior"* ]]
}

@test "helix reverse design --help shows design overview" {
  run "$HELIX_ROOT/cli/helix" reverse design --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"helix reverse design"* ]]
  [[ "$output" == *"R1  skipped for design"* ]]
  [[ "$output" == *"D2-design-dag.yaml"* ]]
}

@test "helix reverse upgrade --help shows upgrade overview" {
  run "$HELIX_ROOT/cli/helix" reverse upgrade --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"upgrade"* ]]
  [[ "$output" == *"Version upgrade impact assessment"* ]]
  [[ "$output" == *"--from <version>"* ]]
}

@test "helix reverse normalization --help shows normalization overview" {
  run "$HELIX_ROOT/cli/helix" reverse normalization --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"normalization"* ]]
  [[ "$output" == *"Design drift normalization"* ]]
}

@test "helix reverse fullback --help shows fullback overview" {
  run "$HELIX_ROOT/cli/helix" reverse fullback --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"fullback"* ]]
  [[ "$output" == *"Post-implementation document alignment"* ]]
}

@test "helix reverse stage help differs for code R1 and design R1" {
  run "$HELIX_ROOT/cli/helix" reverse code R1 --help
  [ "$status" -eq 0 ]
  code_help="$output"
  [[ "$code_help" == *"観測契約の抽出"* ]]
  [[ "$code_help" == *"R1-observed-contracts.yaml"* ]]

  run "$HELIX_ROOT/cli/helix" reverse design R1 --help
  [ "$status" -eq 0 ]
  design_help="$output"
  [[ "$design_help" == *"design は R1 を skip"* ]]
  [[ "$design_help" == *"出力なし"* ]]
  [[ "$design_help" != "$code_help" ]]
}

@test "helix reverse normalization R1 help documents skip" {
  run "$HELIX_ROOT/cli/helix" reverse normalization R1 --help

  [ "$status" -eq 0 ]
  [[ "$output" == *"normalization は R1 を skip"* ]]
  [[ "$output" == *"出力なし"* ]]
}

@test "helix reverse design RGC fail-closes when routing artifact is missing" {
  run "$HELIX_ROOT/cli/helix" reverse design rgc

  [ "$status" -ne 0 ]
  [[ "$output" == *"D4-design-routing.yaml が見つかりません"* ]]
  [[ "$output" == *"先に 'helix reverse design R4' を実行してください"* ]]
}
