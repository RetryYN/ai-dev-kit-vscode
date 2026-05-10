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
count_file="${HELIX_TEST_INVOCATIONS_FILE:-}"
if [ -n "$count_file" ]; then
  count=0
  if [ -f "$count_file" ]; then
    count=$(cat "$count_file")
  fi
  count=$((count + 1))
  printf '%s' "$count" > "$count_file"
fi
printf '%s\n' "${HELIX_TEST_STDOUT:-fake codex ok}"
exit "${HELIX_TEST_CODEX_EXIT:-0}"
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

@test "helix-codex archives codex stdout under .helix/audit/codex-runs" {
  run env \
    HELIX_TEST_STDOUT="audit line" \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "stdout tee" \
    --approved

  [ "$status" -eq 0 ]
  [[ "$output" == *"audit line"* ]]

  shopt -s nullglob
  logs=("$PROJECT_ROOT/.helix/audit/codex-runs"/*.log)
  shopt -u nullglob
  [ "${#logs[@]}" -ge 2 ]
  grep -R -F "audit line" "$PROJECT_ROOT/.helix/audit/codex-runs"
}

@test "helix-codex keeps codex exit code for retry decisions when tee is enabled" {
  invocations="$TMP_ROOT/invocations.txt"

  run env \
    HELIX_TEST_CODEX_EXIT=1 \
    HELIX_TEST_STDOUT="retry line" \
    HELIX_TEST_INVOCATIONS_FILE="$invocations" \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "retry me" \
    --approved \
    --max-retries 1

  [ "$status" -eq 1 ]
  [[ "$output" == *"リトライ (1/1, error=other, backoff=1s)..."* ]]
  [[ "$output" == *"フォールバック: gpt-5.4-mini で再試行"* ]]
  [ "$(cat "$invocations")" -ge 2 ]
}

@test "helix-codex silently falls back to stdout when audit mkdir fails" {
  printf 'not-a-directory\n' > "$PROJECT_ROOT/.helix"

  run env \
    HELIX_TEST_STDOUT="stdout only" \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "mkdir fallback" \
    --approved

  [ "$status" -eq 0 ]
  [[ "$output" == *"stdout only"* ]]
  [ ! -d "$PROJECT_ROOT/.helix/audit/codex-runs" ]
}

@test "helix-codex names audit logs with timestamp role plan and task id" {
  cat > "$BIN_DIR/date" <<'SH'
#!/bin/sh
if [ "$1" = "+%Y%m%d-%H%M%S" ]; then
  printf '%s\n' "20260509-123456"
  exit 0
fi
exec /bin/date "$@"
SH
  chmod +x "$BIN_DIR/date"

  run env \
    HELIX_TEST_STDOUT="named audit" \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "named audit" \
    --approved \
    --plan-id PLAN-034 \
    --task-id W-12

  [ "$status" -eq 0 ]
  [ -f "$PROJECT_ROOT/.helix/audit/codex-runs/20260509-123456-docs-PLAN-034-W-12.log" ]
}
