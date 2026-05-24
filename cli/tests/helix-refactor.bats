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
  git config user.email "refactor@example.com"
  git config user.name "Refactor Test"
  printf "# refactor\n" > README.md
  git add README.md
  git commit -q -m "init"

  "$HELIX_ROOT/cli/helix" init --project-name refactor >/dev/null

  mkdir -p "$PROJECT_ROOT/cli/lib/tests" "$PROJECT_ROOT/cli/lib"
  cat > "$PROJECT_ROOT/cli/lib/sample.py" <<'PY'
def sample():
    return "ok"
PY
  cat > "$PROJECT_ROOT/cli/lib/tests/test_sample.py" <<'PY'
def test_sample():
    assert True
PY
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix refactor help and top-level help include refactor" {
  run "$HELIX_ROOT/cli/helix-refactor" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"helix refactor"* ]]
  [[ "$output" == *"init"* ]]
  [[ "$output" == *"done"* ]]

  run "$HELIX_ROOT/cli/helix" help
  [ "$status" -eq 0 ]
  [[ "$output" == *"refactor"* ]]
}

@test "helix refactor init creates session file" {
  run "$HELIX_ROOT/cli/helix-refactor" init \
    --target cli/lib/sample.py \
    --test-cmd "python3 -c \"print('1 passed in 0.01s')\"" \
    --plan-id L7-cli-helix-refactor-impl
  [ "$status" -eq 0 ]
  [[ "$output" == *"session 開始"* ]]
  [ -f "$PROJECT_ROOT/.helix/refactor-session.json" ]
}

@test "helix refactor status prints active session" {
  "$HELIX_ROOT/cli/helix-refactor" init \
    --target cli/lib/sample.py \
    --test-cmd "python3 -c \"print('1 passed in 0.01s')\"" \
    --plan-id L7-cli-helix-refactor-impl >/dev/null

  run "$HELIX_ROOT/cli/helix-refactor" status
  [ "$status" -eq 0 ]
  [[ "$output" == *"session_id:"* ]]
  [[ "$output" == *"cli/lib/sample.py"* ]]
}

@test "helix refactor check reports green baseline" {
  "$HELIX_ROOT/cli/helix-refactor" init \
    --target cli/lib/sample.py \
    --test-cmd "python3 -c \"print('1 passed in 0.01s')\"" \
    --plan-id L7-cli-helix-refactor-impl >/dev/null

  run "$HELIX_ROOT/cli/helix-refactor" check
  [ "$status" -eq 0 ]
  [[ "$output" == *"振る舞い不変"* ]]
}

@test "helix refactor done removes session file" {
  "$HELIX_ROOT/cli/helix-refactor" init \
    --target cli/lib/sample.py \
    --test-cmd "python3 -c \"print('1 passed in 0.01s')\"" \
    --plan-id L7-cli-helix-refactor-impl >/dev/null

  run "$HELIX_ROOT/cli/helix-refactor" done
  [ "$status" -eq 0 ]
  [[ "$output" == *"session 完了"* ]]
  [ ! -f "$PROJECT_ROOT/.helix/refactor-session.json" ]
}

@test "helix refactor check without session exits 2 and commands check passes" {
  run "$HELIX_ROOT/cli/helix-refactor" check
  [ "$status" -eq 2 ]
  [[ "$output" == *"no active refactor session"* ]]

  run "$HELIX_ROOT/cli/helix" commands check
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: command catalog is consistent"* ]]
}
