#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

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

@test "usage limit は layer 1 枯渇後に auto-fallback role chain へ進む" {
  invocations="$TMP_ROOT/invocations.txt"
  args_file="$TMP_ROOT/args.log"

  run env \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_INVOCATIONS_FILE="$invocations" \
    HELIX_TEST_ARGS_FILE="$args_file" \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on default fallback" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    HELIX_TEST_STDERR_3="hit your usage limit on pe primary" \
    HELIX_TEST_CODEX_EXIT_3=1 \
    HELIX_TEST_STDOUT_4="se primary succeeded" \
    HELIX_TEST_CODEX_EXIT_4=0 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role pg \
    --task "usage limit auto fallback" \
    --approved \
    --max-retries 0

  [ "$status" -eq 0 ]
  [ "$(cat "$invocations")" -eq 4 ]
  [[ "$output" == *"Primary (gpt-5.3-codex-spark) 失敗。フォールバック: gpt-5.4-mini で再試行"* ]]
  [[ "$output" == *"auto-fallback: role pg -> pe (model=gpt-5.3-codex)"* ]]
  [[ "$output" == *"auto-fallback: role pg -> se (model=gpt-5.4)"* ]]
  [[ "$output" == *"auto-fallback 成功: role se (model=gpt-5.4)"* ]]
  [[ "$(cat "$args_file")" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(cat "$args_file")" == *"call=2 model=gpt-5.4-mini"* ]]
  [[ "$(cat "$args_file")" == *"call=3 model=gpt-5.3-codex"* ]]
  [[ "$(cat "$args_file")" == *"call=4 model=gpt-5.4"* ]]
  grep -Rqi "hit your usage limit" "$PROJECT_ROOT/.helix/audit/codex-runs"
}

@test "AUTO_FALLBACK 未設定では usage limit でも layer 2 は発火しない" {
  invocations="$TMP_ROOT/invocations.txt"
  args_file="$TMP_ROOT/args.log"

  run env \
    HELIX_TEST_INVOCATIONS_FILE="$invocations" \
    HELIX_TEST_ARGS_FILE="$args_file" \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on default fallback" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role pg \
    --task "usage limit without auto fallback" \
    --approved \
    --max-retries 0

  [ "$status" -eq 1 ]
  [ "$(cat "$invocations")" -eq 2 ]
  [[ "$output" != *"auto-fallback:"* ]]
  [[ "$(cat "$args_file")" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(cat "$args_file")" == *"call=2 model=gpt-5.4-mini"* ]]
}

@test "usage limit 以外のエラーでは AUTO_FALLBACK=1 でも layer 2 を試さない" {
  invocations="$TMP_ROOT/invocations.txt"
  args_file="$TMP_ROOT/args.log"

  run env \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_INVOCATIONS_FILE="$invocations" \
    HELIX_TEST_ARGS_FILE="$args_file" \
    HELIX_TEST_STDERR_1="backend exploded" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="still not usage limit" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role pg \
    --task "non usage limit error" \
    --approved \
    --max-retries 0

  [ "$status" -eq 1 ]
  [ "$(cat "$invocations")" -eq 2 ]
  [[ "$output" != *"auto-fallback:"* ]]
  [[ "$(cat "$args_file")" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(cat "$args_file")" == *"call=2 model=gpt-5.4-mini"* ]]
}

@test "--fallback-model 明示時は layer 0 を優先し、枯渇後に layer 2 へ進む" {
  invocations="$TMP_ROOT/invocations.txt"
  args_file="$TMP_ROOT/args.log"

  run env \
    HELIX_CODEX_AUTO_FALLBACK=1 \
    HELIX_TEST_INVOCATIONS_FILE="$invocations" \
    HELIX_TEST_ARGS_FILE="$args_file" \
    HELIX_TEST_STDERR_1="hit your usage limit on pg primary" \
    HELIX_TEST_CODEX_EXIT_1=1 \
    HELIX_TEST_STDERR_2="hit your usage limit on explicit fallback" \
    HELIX_TEST_CODEX_EXIT_2=1 \
    HELIX_TEST_STDOUT_3="pe primary succeeded" \
    HELIX_TEST_CODEX_EXIT_3=0 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role pg \
    --task "explicit fallback model wins" \
    --approved \
    --max-retries 0 \
    --fallback-model gpt-5.5

  [ "$status" -eq 0 ]
  [ "$(cat "$invocations")" -eq 3 ]
  [[ "$output" == *"フォールバック: gpt-5.5 で再試行"* ]]
  [[ "$output" == *"auto-fallback: role pg -> pe (model=gpt-5.3-codex)"* ]]
  [[ "$(cat "$args_file")" == *"call=1 model=gpt-5.3-codex-spark"* ]]
  [[ "$(cat "$args_file")" == *"call=2 model=gpt-5.5"* ]]
  [[ "$(cat "$args_file")" == *"call=3 model=gpt-5.3-codex"* ]]
  [[ "$(cat "$args_file")" != *"gpt-5.4-mini"* ]]
}
