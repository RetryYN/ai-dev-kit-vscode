#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  while IFS='=' read -r name _; do
    [[ "$name" == HELIX_TEST_* ]] && unset "$name"
  done < <(env)
  unset CODEX_BIN HELIX_CODEX_BIN HELIX_CODEX_AUTO_FALLBACK HELIX_CODEX_NO_FOOTER
  unset HELIX_CODEX_INTERNAL HELIX_DISABLE_SPARK HELIX_MODEL_OVERRIDE

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$BIN_DIR"

  cat > "$BIN_DIR/codex" <<'SH'
#!/bin/sh
set -eu
printf '%s\n' '---SUMMARY_START---'
printf '%s\n' 'decision: passed'
printf '%s\n' 'files: cli/lib/codex_post_validation.py'
printf '%s\n' "${HELIX_TEST_DIFF_LINES:-diff_lines: 1}"
printf '%s\n' 'tests: fake'
printf '%s\n' 'intermediate_errors: なし'
printf '%s\n' 'remaining: なし'
printf '%s\n' '---SUMMARY_END---'
SH
  chmod +x "$BIN_DIR/codex"

  cd "$PROJECT_ROOT"
  git init -q
  git config user.email test@example.com
  git config user.name "Test User"
  printf 'tracked\n' > tracked.txt
  git add tracked.txt
  git commit -qm "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:$HELIX_ROOT/cli:$PATH"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "impl_task_no_diff_keeps summary output without warning" {
  run env \
    HELIX_DYNAMIC_SKILLS=0 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role pg \
    --task $'[タスク種別] 実装\nwrite audit test' \
    --approved \
    --max-retries 0

  [ "$status" -eq 0 ]
  [[ "$output" == *"---SUMMARY_START---"* ]]
  [[ "$output" == *"diff_lines: 1"* ]]
  [[ "$output" != *"WARNING: audit-only failure suspected"* ]]
}

@test "review_task_no_diff_silent" {
  run env \
    HELIX_DYNAMIC_SKILLS=0 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role pg \
    --task $'[タスク種別] レビュー\nwrite audit test' \
    --approved \
    --max-retries 0

  [ "$status" -eq 0 ]
  [[ "$output" != *"WARNING:"* ]]
}
