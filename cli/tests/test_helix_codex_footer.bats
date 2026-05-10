#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  while IFS='=' read -r name _; do
    [[ "$name" == HELIX_TEST_* ]] && unset "$name"
  done < <(env)
  unset CODEX_BIN HELIX_CODEX_BIN HELIX_CODEX_AUTO_FALLBACK HELIX_CODEX_NO_FOOTER
  unset HELIX_CODEX_INTERNAL HELIX_DISABLE_SPARK HELIX_MODEL_OVERRIDE
  unset HELIX_STDOUT_FILE HELIX_STDERR_FILE

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
count_file="${HELIX_TEST_INVOCATIONS_FILE:-}"
args_file="${HELIX_TEST_ARGS_FILE:-}"
call=1
model=""
prev=""

if [ -n "$count_file" ] && [ -f "$count_file" ]; then
  call=$(($(cat "$count_file") + 1))
fi
if [ -n "$count_file" ]; then
  printf '%s' "$call" > "$count_file"
fi

for arg in "$@"; do
  if [ "$prev" = "-m" ]; then
    model="$arg"
    break
  fi
  prev="$arg"
done

if [ -n "$args_file" ]; then
  printf 'call=%s model=%s\n' "$call" "$model" >> "$args_file"
fi

stdout="$(printenv "HELIX_TEST_STDOUT_$call" || true)"
stderr="$(printenv "HELIX_TEST_STDERR_$call" || true)"
exit_code="$(printenv "HELIX_TEST_CODEX_EXIT_$call" || printf '0')"

[ -n "$stdout" ] && printf '%b' "$stdout"
[ -n "$stderr" ] && printf '%b' "$stderr" >&2
exit "$exit_code"
SH
  chmod +x "$BIN_DIR/codex"

  cd "$PROJECT_ROOT"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:$HELIX_ROOT/cli:$PATH"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

run_runtime_case() {
  STDOUT_FILE="$TMP_ROOT/runtime.stdout"
  STDERR_FILE="$TMP_ROOT/runtime.stderr"
  INVOCATIONS_FILE="$TMP_ROOT/invocations.txt"
  ARGS_FILE="$TMP_ROOT/args.log"
  local task="$1"
  local env_args=()
  local cli_args=()
  local parsing_env=true
  shift

  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "--" ]]; then
      parsing_env=false
      shift
      continue
    fi
    if [[ "$parsing_env" == true ]]; then
      env_args+=("$1")
    else
      cli_args+=("$1")
    fi
    shift
  done

  run env \
    HELIX_DYNAMIC_SKILLS=0 \
    HELIX_TEST_INVOCATIONS_FILE="$INVOCATIONS_FILE" \
    HELIX_TEST_ARGS_FILE="$ARGS_FILE" \
    HELIX_STDOUT_FILE="$STDOUT_FILE" \
    HELIX_STDERR_FILE="$STDERR_FILE" \
    "${env_args[@]}" \
    bash -c '"$1" --role pg --task "$2" --approved --max-retries 0 "${@:3}" >"$HELIX_STDOUT_FILE" 2>"$HELIX_STDERR_FILE"' _ \
    "$HELIX_ROOT/cli/helix-codex" \
    "$task" \
    "${cli_args[@]}"
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
  [[ "$output" == *$'## 出力フォーマット (helix-codex 自動付加、上書き禁止)\n\n**重要 (最優先)**: 最終 summary block 全体を `---SUMMARY_START---` / `---SUMMARY_END---` で必ず囲むこと。'* ]]
  [[ "$output" == *"---SUMMARY_START---"* ]]
  [[ "$output" == *"---SUMMARY_END---"* ]]
  [[ "$output" == *"summary は 5 行以内で末尾に置く"* ]]
  [[ "$output" == *"decision (passed/failed/blocked/changes_required)"* ]]
  [[ "$output" == *"tail -30"* ]]
}

@test "helix-codex footer includes clean checkout and intermediate error guidance" {
  run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer verification guidance" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"tests: は clean checkout 後"* ]]
  [[ "$output" == *"intermediate_errors:"* ]]
  [[ "$output" == *"dirty workspace 由来 fail"* ]]
}

@test "helix-codex footer includes concrete summary output example" {
  run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer example" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"### 出力例 (これに従う、実際の出力では"* ]]
  [[ "$output" == *"(作業内容の自由記述、進行ログ、差分等はここに書く)"* ]]
  [[ "$output" == *"files: cli/helix-codex, cli/tests/test_helix_codex_footer.bats"* ]]
  [[ "$output" == *"tests: clean checkout 後 bats 7/7 PASS"* ]]
  [[ "$output" == *"intermediate_errors: なし"* ]]
  [[ "$output" == *"remaining: なし"* ]]
}

@test "helix-codex dry-run shows both discipline prompt and output footer" {
  run "$HELIX_ROOT/cli/helix-codex" --role pg --task "footer coexist" --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"## Codex Mandatory Discipline"* ]]
  [[ "$output" == *"No Commit (委譲 Codex 限定ルール)"* ]]
  [[ "$output" == *"## 出力フォーマット (helix-codex 自動付加、上書き禁止)"* ]]
}

@test "marker 付き summary block のみを parent stdout に出す" {
  run_runtime_case "summary marker runtime" \
    HELIX_TEST_STDOUT_1=$'progress line\n---SUMMARY_START---\ndecision: passed\nfiles:\n- cli/helix-codex\ntests: bats\nintermediate_errors: none\nremaining: none\n---SUMMARY_END---\n' \
    HELIX_TEST_STDERR_1=$'wrapper stderr\n'

  [ "$status" -eq 0 ]
  [[ "$(cat "$STDOUT_FILE")" == *"---SUMMARY_START---"* ]]
  [[ "$(cat "$STDOUT_FILE")" == *"decision: passed"* ]]
  [[ "$(cat "$STDOUT_FILE")" != *"progress line"* ]]
  [[ "$(cat "$STDOUT_FILE")" != *"wrapper stderr"* ]]
  grep -q 'wrapper stderr' "$STDERR_FILE"
  grep -R -q 'progress line' "$PROJECT_ROOT/.helix/audit/codex-runs"
}

@test "summary marker 欠落時は末尾30行へ fallback して warning を stderr に出す" {
  local payload=""
  local i
  for i in $(seq 1 35); do
    printf -v payload '%sline %02d\n' "$payload" "$i"
  done

  run_runtime_case "summary fallback runtime" \
    "HELIX_TEST_STDOUT_1=$payload"

  [ "$status" -eq 0 ]
  line_count="$(awk 'END {print NR}' "$STDOUT_FILE")"
  [ "$line_count" -ge 29 ]
  [ "$line_count" -le 30 ]
  grep -q '^line 06$' "$STDOUT_FILE"
  grep -q 'line 35$' "$STDOUT_FILE"
  ! grep -q '^line 05$' "$STDOUT_FILE"
  grep -q 'summary marker missing, falling back to last 30 lines' "$STDERR_FILE"
  grep -R -q '^line 01$' "$PROJECT_ROOT/.helix/audit/codex-runs"
}
