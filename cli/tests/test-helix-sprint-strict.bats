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
  mkdir -p "$PROJECT_ROOT/.helix" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  echo "# sprint strict" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'YAML'
project: sprint-strict-test
sprint:
  current_step: .5
  status: active
  drive: be
  tracks: null
  phase: null
  phase_b:
    current_step: null
    status: pending
    steps:
      .b1: { status: pending }
      .b2: { status: pending }
      .b3: { status: pending }
  steps:
    .1a: { status: completed }
    .1b: { status: completed }
    .2: { status: completed }
    .3: { status: completed }
    .4: { status: completed }
    .5: { status: pending }
  ui: false
YAML

  cat > "$PROJECT_ROOT/.helix/framework.yaml" <<'YAML'
detected: unknown
tools: {}
YAML
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

current_step() {
  value="$(python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/phase.yaml" sprint.current_step)"
  case "$value" in
    0.2) echo ".2" ;;
    0.3) echo ".3" ;;
    0.4) echo ".4" ;;
    0.5) echo ".5" ;;
    *) echo "$value" ;;
  esac
}

step_status() {
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/phase.yaml" sprint.steps..5.status
}

@test "drift なしなら complete 成功して strict 4項目を出力する" {
  run env \
    HELIX_SPRINT_LINT_CMD="true" \
    HELIX_SPRINT_TEST_CMD="true" \
    HELIX_SPRINT_BUILD_CMD="true" \
    "$HELIX_ROOT/cli/helix-sprint" complete

  [ "$status" -eq 0 ]
  [[ "$output" == *"[strict] lint: ok"* ]]
  [[ "$output" == *"[strict] test: ok"* ]]
  [[ "$output" == *"[strict] build: ok"* ]]
  [[ "$output" == *"[strict] drift-check: ok"* ]]
  [ "$(current_step)" = "completed" ]
  [ "$(step_status)" = "completed" ]
}

@test "drift ありなら complete は失敗して .5 を維持する" {
  mkdir -p "$PROJECT_ROOT/docs/features/auth/D-AUDIT"
  printf 'audit note\n' > "$PROJECT_ROOT/docs/features/auth/D-AUDIT/custom.md"

  run env \
    HELIX_SPRINT_LINT_CMD="true" \
    HELIX_SPRINT_TEST_CMD="true" \
    HELIX_SPRINT_BUILD_CMD="true" \
    "$HELIX_ROOT/cli/helix-sprint" complete

  [ "$status" -ne 0 ]
  [[ "$output" == *"[strict] drift-check: failed"* ]]
  [ "$(current_step)" = ".5" ]
  [ "$(step_status)" = "pending" ]
}

@test "lint 失敗なら complete は blocked される" {
  run env \
    HELIX_SPRINT_LINT_CMD="echo lint boom >&2; exit 9" \
    HELIX_SPRINT_TEST_CMD="true" \
    HELIX_SPRINT_BUILD_CMD="true" \
    "$HELIX_ROOT/cli/helix-sprint" complete

  [ "$status" -ne 0 ]
  [[ "$output" == *"[strict] lint: failed"* ]]
  [ "$(current_step)" = ".5" ]
}

@test "test 失敗なら complete は blocked される" {
  run env \
    HELIX_SPRINT_LINT_CMD="true" \
    HELIX_SPRINT_TEST_CMD="echo test boom >&2; exit 7" \
    HELIX_SPRINT_BUILD_CMD="true" \
    "$HELIX_ROOT/cli/helix-sprint" complete

  [ "$status" -ne 0 ]
  [[ "$output" == *"[strict] test: failed"* ]]
  [ "$(current_step)" = ".5" ]
}

@test "build 失敗なら complete は blocked される" {
  run env \
    HELIX_SPRINT_LINT_CMD="true" \
    HELIX_SPRINT_TEST_CMD="true" \
    HELIX_SPRINT_BUILD_CMD="echo build boom >&2; exit 5" \
    "$HELIX_ROOT/cli/helix-sprint" complete

  [ "$status" -ne 0 ]
  [[ "$output" == *"[strict] build: failed"* ]]
  [ "$(current_step)" = ".5" ]
}
