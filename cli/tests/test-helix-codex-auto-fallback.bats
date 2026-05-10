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

[ -n "$stdout" ] && printf '%s\n' "$stdout"
[ -n "$stderr" ] && printf '%s\n' "$stderr" >&2
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

run_case_for_role() {
  local role="$1"
  shift
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
    "${env_args[@]}" \
    "$HELIX_ROOT/cli/helix-codex" \
    --role "$role" \
    --task "$task" \
    --approved \
    --max-retries 0 \
    "${cli_args[@]}"
}

run_case() {
  run_case_for_role pg "$@"
}

args_log() {
  cat "$ARGS_FILE"
}

summary_block() {
  cat <<'EOF'
---SUMMARY_START---
decision: passed
files:
- cli/helix-codex
tests: bats
intermediate_errors: none
remaining: none
---SUMMARY_END---
EOF
}

@test "usage_limit + AUTO_FALLBACK=1 + --fallback-model では Layer 0 が最優先" {
  run_case "explicit fallback precedes layer2" \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on explicit fallback" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    HELIX_TEST_STDOUT_3="pe primary succeeded" \
    HELIX_TEST_CODEX_EXIT_3=0 \
    -- \
    --fallback-model gpt-5.5

  [ "$status" -eq 0 ]
  [ "$(cat "$INVOCATIONS_FILE")" -eq 3 ]
  [[ "$output" == *"フォールバック: gpt-5.5 で再試行"* ]]
  [[ "$output" == *"auto-fallback: role pg -> pe (model=gpt-5.3-codex)"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(args_log)" == *"call=2 model=gpt-5.5"* ]]
  [[ "$(args_log)" == *"call=3 model=gpt-5.3-codex"* ]]
  [[ "$(args_log)" != *"gpt-5.4-mini"* ]]
}

@test "usage_limit + AUTO_FALLBACK=1 では Layer 2 が Layer 1 より先に発火する" {
  run_case "usage limit auto fallback" \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on pe primary" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    HELIX_TEST_STDOUT_3="se primary succeeded" \
    HELIX_TEST_CODEX_EXIT_3=0

  [ "$status" -eq 0 ]
  [ "$(cat "$INVOCATIONS_FILE")" -eq 3 ]
  [[ "$output" == *"auto-fallback: role pg -> pe (model=gpt-5.3-codex)"* ]]
  [[ "$output" == *"auto-fallback 成功: role se (model=gpt-5.4)"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(args_log)" == *"call=2 model=gpt-5.3-codex"* ]]
  [[ "$(args_log)" == *"call=3 model=gpt-5.4"* ]]
  [[ "$(args_log)" != *"gpt-5.4-mini"* ]]
  grep -Rqi "hit your usage limit" "$PROJECT_ROOT/.helix/audit/codex-runs"
}

@test "usage_limit + AUTO_FALLBACK=0 では Layer 1 だけが発火する" {
  run_case "usage limit without auto fallback" \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on default fallback" \
    HELIX_TEST_CODEX_EXIT_2=1

  [ "$status" -eq 1 ]
  [ "$(cat "$INVOCATIONS_FILE")" -eq 2 ]
  [[ "$output" != *"auto-fallback:"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(args_log)" == *"call=2 model=gpt-5.4-mini"* ]]
}

@test "rate_limit + AUTO_FALLBACK=1 では Layer 2 を試さず Layer 1 へ進む" {
  run_case "rate limit skips auto fallback" \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_STDERR_1="rate limit exceeded on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="rate limit exceeded on default fallback" \
    HELIX_TEST_CODEX_EXIT_2=1

  [ "$status" -eq 1 ]
  [ "$(cat "$INVOCATIONS_FILE")" -eq 2 ]
  [[ "$output" != *"auto-fallback:"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(args_log)" == *"call=2 model=gpt-5.4-mini"* ]]
}

@test "Layer 2 chain 全失敗時は Layer 1 default_fallback に復帰する" {
  run_case "auto fallback falls back to registry default" \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on pe primary" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    HELIX_TEST_STDERR_3="hit your usage limit on se primary" \
    HELIX_TEST_CODEX_EXIT_3=1 \
    HELIX_TEST_STDERR_4="hit your usage limit on default fallback" \
    HELIX_TEST_CODEX_EXIT_4=1

  [ "$status" -eq 1 ]
  [ "$(cat "$INVOCATIONS_FILE")" -eq 4 ]
  [[ "$output" == *"auto-fallback: role pg -> pe (model=gpt-5.3-codex)"* ]]
  [[ "$output" == *"auto-fallback: role pg -> se (model=gpt-5.4)"* ]]
  [[ "$output" == *"フォールバック: gpt-5.4-mini で再試行"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(args_log)" == *"call=2 model=gpt-5.3-codex"* ]]
  [[ "$(args_log)" == *"call=3 model=gpt-5.4"* ]]
  [[ "$(args_log)" == *"call=4 model=gpt-5.4-mini"* ]]
}

@test "HELIX_DISABLE_SPARK=1 + docs role dry-run では spark が一度も出ない" {
  run env HELIX_DYNAMIC_SKILLS=0 HELIX_DISABLE_SPARK=1 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "docs dry-run disable spark" \
    --dry-run

  [ "$status" -eq 0 ]
  [[ "$output" == *"Model:     gpt-5.3-codex"* ]]
  [[ "$output" != *"gpt-5.3-codex-spark"* ]]
}

@test "HELIX_DISABLE_SPARK=1 + HELIX_MODEL_OVERRIDE=spark では warning を出して spark を優先する" {
  local summary
  summary="$(summary_block)"

  run_case "override beats disable spark" \
    HELIX_DISABLE_SPARK=1 \
    HELIX_MODEL_OVERRIDE=spark \
    "HELIX_TEST_STDOUT_1=$summary"

  [ "$status" -eq 0 ]
  [[ "$output" == *"HELIX_DISABLE_SPARK=1"* ]]
  [[ "$output" == *"gpt-5.3-codex-spark"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex-spark"* ]]
}

@test "HELIX_DISABLE_SPARK=1 + auto_fallback usage_limit では chain でも spark を試行しない" {
  local summary
  summary="$(summary_block)"

  run_case "disable spark skips spark in auto fallback" \
    HELIX_DISABLE_SPARK=1 \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    "HELIX_TEST_STDOUT_2=$summary"

  [ "$status" -eq 0 ]
  [ "$(cat "$INVOCATIONS_FILE")" -eq 2 ]
  [[ "$output" == *"auto-fallback: role pg -> se (model=gpt-5.4)"* ]]
  [[ "$(args_log)" == *"call=1 model=gpt-5.3-codex"* ]]
  [[ "$(args_log)" == *"call=2 model=gpt-5.4"* ]]
  [[ "$(args_log)" != *"gpt-5.3-codex-spark"* ]]
}
