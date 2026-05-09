#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"

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
pre_sleep="${HELIX_TEST_PRE_SLEEP:-0}"
post_sleep="${HELIX_TEST_POST_SLEEP:-0}"
touch_path="${HELIX_TEST_TOUCH:-}"
touch_mode="${HELIX_TEST_TOUCH_MODE:-append}"
touch_content="${HELIX_TEST_TOUCH_CONTENT:-changed}"

if [ "$pre_sleep" != "0" ]; then
  sleep "$pre_sleep"
fi

if [ -n "$touch_path" ]; then
  mkdir -p "$(dirname "$touch_path")"
  case "$touch_mode" in
    touch)
      touch "$touch_path"
      ;;
    *)
      printf '%s\n' "$touch_content" >> "$touch_path"
      ;;
  esac
fi

if [ "$post_sleep" != "0" ]; then
  sleep "$post_sleep"
fi

printf 'fake codex ok\n'
SH
  chmod +x "$BIN_DIR/codex"

  cd "$PROJECT_ROOT"
  git init -q
  git config user.email test@example.com
  git config user.name "Test User"
  printf 'allowed\n' > tracked-a.txt
  printf 'other\n' > tracked-b.txt
  git add tracked-a.txt tracked-b.txt
  git commit -qm "init"

  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:$HELIX_ROOT/cli:$PATH"
}

teardown() {
  stop_alive_process
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

start_alive_process() {
  sleep 10 &
  ALIVE_PID=$!
}

stop_alive_process() {
  if [ -n "${ALIVE_PID:-}" ]; then
    kill "$ALIVE_PID" 2>/dev/null || true
    wait "$ALIVE_PID" 2>/dev/null || true
    ALIVE_PID=""
  fi
}

write_plan_baseline() {
  local baseline_path="$1"
  local plan_id="$2"

  mkdir -p "$(dirname "$baseline_path")"
  cat > "$baseline_path" <<EOF
# plan_id: $plan_id
tracked-a.txt
EOF
}

write_same_plan_audit_log() {
  local plan_id="$1"
  local label="$2"
  local pid="${3:-${ALIVE_PID:-$$}}"

  mkdir -p "$PROJECT_ROOT/.helix/audit/codex-runs"
  cat > "$PROJECT_ROOT/.helix/audit/codex-runs/20260510-010203-docs-${plan_id}-${label}.log" <<EOF
# pid: $pid
# plan_id: $plan_id
other process for $plan_id
EOF
}

run_tracked_b_change_case() {
  local expected_status="$1"
  shift

  run env \
    HELIX_TEST_TOUCH=tracked-b.txt \
    HELIX_TEST_TOUCH_CONTENT=changed \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "concurrent case" \
    --approved \
    --allowed-files "tracked-a.txt" \
    "$@"

  [ "$status" -eq "$expected_status" ]
}

@test "same plan positive auto-adds trusted concurrent baseline" {
  start_alive_process
  write_same_plan_audit_log "PLAN-039" "peer"
  write_plan_baseline \
    "$PROJECT_ROOT/.helix/tmp/codex-baseline-${ALIVE_PID}-111111111.txt" \
    "PLAN-039"

  run_tracked_b_change_case 0 --plan-id PLAN-039
  [[ "$output" == *"auto-detect: plan=PLAN-039 baseline=1 file(s)"* ]]
}

@test "different plan negative does not auto-add baseline" {
  start_alive_process
  write_same_plan_audit_log "PLAN-OTHER" "peer"
  write_plan_baseline \
    "$PROJECT_ROOT/.helix/tmp/codex-baseline-${ALIVE_PID}-111111111.txt" \
    "PLAN-OTHER"

  run_tracked_b_change_case 1 --plan-id PLAN-039
  [[ "$output" == *"--allowed-files 外の変更を検出しました"* ]]
  [[ "$output" != *"auto-detect: plan=PLAN-039 baseline=1 file(s)"* ]]
}

@test "no plan-id negative skips auto-detect" {
  start_alive_process
  write_same_plan_audit_log "PLAN-039" "peer"
  write_plan_baseline \
    "$PROJECT_ROOT/.helix/tmp/codex-baseline-${ALIVE_PID}-111111111.txt" \
    "PLAN-039"

  run_tracked_b_change_case 1
  [[ "$output" == *"--allowed-files 外の変更を検出しました"* ]]
  [[ "$output" != *"auto-detect: plan=PLAN-039 baseline=1 file(s)"* ]]
}

@test "stale pid negative rejects dead baseline candidate" {
  write_same_plan_audit_log "PLAN-039" "peer" "999999"
  write_plan_baseline \
    "$PROJECT_ROOT/.helix/tmp/codex-baseline-999999-111111111.txt" \
    "PLAN-039"

  run_tracked_b_change_case 1 --plan-id PLAN-039
  [[ "$output" == *"--allowed-files 外の変更を検出しました"* ]]
  [[ "$output" != *"auto-detect: plan=PLAN-039 baseline=1 file(s)"* ]]
}

@test "forged baseline reject ignores outside trust boundary" {
  start_alive_process
  write_same_plan_audit_log "PLAN-039" "peer"
  mkdir -p "$TMP_ROOT/forged"
  write_plan_baseline \
    "$TMP_ROOT/forged/codex-baseline-${ALIVE_PID}-111111111.txt" \
    "PLAN-039"

  run_tracked_b_change_case 1 --plan-id PLAN-039
  [[ "$output" == *"--allowed-files 外の変更を検出しました"* ]]
  [[ "$output" != *"auto-detect: plan=PLAN-039 baseline=1 file(s)"* ]]
}

@test "symlink reject ignores linked baseline candidate" {
  start_alive_process
  write_same_plan_audit_log "PLAN-039" "peer"
  write_plan_baseline "$TMP_ROOT/target-baseline.txt" "PLAN-039"
  mkdir -p "$PROJECT_ROOT/.helix/tmp"
  ln -s "$TMP_ROOT/target-baseline.txt" \
    "$PROJECT_ROOT/.helix/tmp/codex-baseline-${ALIVE_PID}-111111111.txt"

  run_tracked_b_change_case 1 --plan-id PLAN-039
  [[ "$output" == *"--allowed-files 外の変更を検出しました"* ]]
  [[ "$output" != *"auto-detect: plan=PLAN-039 baseline=1 file(s)"* ]]
}

@test "codex allowed-files rejects out-of-scope new file" {
  run env \
    HELIX_TEST_TOUCH=rogue.txt \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "new file" \
    --approved \
    --allowed-files "tracked-a.txt"

  [ "$status" -eq 1 ]
  [[ "$output" == *"--allowed-files 外の変更を検出しました"* ]]
  [[ "$output" == *"rogue.txt"* ]]
}

@test "baseline existing untracked file touch is ignored" {
  printf 'existing\n' > preexisting.log

  run env \
    HELIX_TEST_TOUCH=preexisting.log \
    HELIX_TEST_TOUCH_MODE=touch \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "touch baseline untracked" \
    --approved \
    --allowed-files "tracked-a.txt"

  [ "$status" -eq 0 ]
}
