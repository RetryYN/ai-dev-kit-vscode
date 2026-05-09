#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  HELIX_TMP_HOME="$TMP_ROOT/helix-home"
  FAKE_BIN="$TMP_ROOT/bin"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$HELIX_TMP_HOME/cli" "$FAKE_BIN"

  ln -s "$HELIX_ROOT/cli/helix" "$HELIX_TMP_HOME/cli/helix"
  ln -s "$HELIX_ROOT/cli/helix-claude" "$HELIX_TMP_HOME/cli/helix-claude"
  ln -s "$HELIX_ROOT/cli/claude" "$HELIX_TMP_HOME/cli/claude"
  ln -s "$HELIX_ROOT/cli/lib" "$HELIX_TMP_HOME/cli/lib"
  ln -s "$HELIX_ROOT/cli/templates" "$HELIX_TMP_HOME/cli/templates"
  mkdir -p "$HELIX_TMP_HOME/cli/roles"

  cat > "$HELIX_TMP_HOME/cli/roles/pmo-sonnet.conf" <<'CONF'
claude_model=claude-sonnet-4-6
claude_thinking=medium
claude_permission_mode=plan
claude_disallowed_tools="Edit,Write,NotebookEdit"
skills=(
)
common_docs=(
)
system_prompt="PMO Sonnet"
CONF

  cat > "$HELIX_TMP_HOME/cli/roles/pmo-haiku.conf" <<'CONF'
claude_model=claude-haiku-4-5-20251001
claude_thinking=low
claude_permission_mode=acceptEdits
claude_allow_paths="docs/**,skills/**"
skills=(
)
common_docs=(
)
system_prompt="PMO Haiku"
CONF

  cd "$PROJECT_ROOT"
  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"
  echo "init" > README.md
  git add README.md
  git commit -q -m "init"
  mkdir -p .helix
  cat > .helix/phase.yaml <<'YAML'
project: pmo-test
current_phase: L4
sprint:
  current_step: .2
  status: active
YAML

  export HELIX_HOME="$HELIX_TMP_HOME"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$HELIX_TMP_HOME/cli:$FAKE_BIN:$PATH"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

write_fake_claude() {
  local exit_code="${1:-0}"
  local sleep_seconds="${2:-0}"
  cat > "$FAKE_BIN/claude" <<SH
#!/bin/sh
printf '%s\n' "\$*" > "$TMP_ROOT/claude.args"
if [ "$sleep_seconds" != "0" ]; then
  sleep "$sleep_seconds"
fi
printf 'fake claude ok\n'
exit "$exit_code"
SH
  chmod +x "$FAKE_BIN/claude"
}

@test "helix claude pmo sonnet execute smoke writes log" {
  write_fake_claude 0

  run "$HELIX_TMP_HOME/cli/helix" claude --role pmo --model sonnet --task "ping" --execute

  [ "$status" -eq 0 ]
  [[ "$output" == *"[helix-claude] execute log:"* ]]
  grep -q -- "--model claude-sonnet-4-6" "$TMP_ROOT/claude.args"
  grep -q -- "--permission-mode plan" "$TMP_ROOT/claude.args"
  ls "$PROJECT_ROOT"/.helix/cache/pmo/*.log >/dev/null
}

@test "helix claude pmo haiku execute with allow paths uses acceptEdits" {
  write_fake_claude 0

  run "$HELIX_TMP_HOME/cli/helix" claude --role pmo --model haiku --task "ping" --execute --allow-paths "docs/**"

  [ "$status" -eq 0 ]
  grep -q -- "--model claude-haiku-4-5-20251001" "$TMP_ROOT/claude.args"
  grep -q -- "--permission-mode acceptEdits" "$TMP_ROOT/claude.args"
  grep -q -- "docs/**" "$TMP_ROOT/claude.args"
}

@test "helix claude pmo execute propagates auth failure code" {
  write_fake_claude 2

  run "$HELIX_TMP_HOME/cli/helix" claude --role pmo --model sonnet --task "ping" --execute

  [ "$status" -eq 2 ]
  [[ "$output" == *"[helix-claude] execute log:"* ]]
}

@test "helix claude pmo execute timeout returns 124" {
  write_fake_claude 0 5

  run "$HELIX_TMP_HOME/cli/helix" claude --role pmo --model sonnet --task "slow" --execute --timeout 1

  [ "$status" -eq 124 ]
  [[ "$output" == *"[helix-claude] execute log:"* ]]
}

@test "helix claude pmo dry-run remains default compatible" {
  run "$HELIX_TMP_HOME/cli/helix" claude --role pmo --task "dry ping" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"helix-claude dry-run"* ]]
  [[ "$output" == *"Role:    pmo-sonnet"* ]]
  [[ "$output" == *"PMO プロンプト基盤"* ]]
}
