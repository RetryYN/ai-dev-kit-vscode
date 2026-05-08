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
  rm -rf "$TMP_ROOT"
}

@test "parallel helix-codex tracked change does not trigger false positive" {
  HELIX_TEST_POST_SLEEP=0.3 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "A task" \
    --approved \
    --allowed-files "tracked-a.txt" \
    >"$TMP_ROOT/a.out" 2>&1 &
  pid_a=$!

  sleep 0.05

  HELIX_TEST_TOUCH=tracked-b.txt \
    HELIX_TEST_POST_SLEEP=0.5 \
    "$HELIX_ROOT/cli/helix-codex" \
    --role docs \
    --task "B task" \
    --approved \
    --allowed-files "tracked-b.txt" \
    >"$TMP_ROOT/b.out" 2>&1 &
  pid_b=$!

  wait "$pid_a"
  status_a=$?
  wait "$pid_b"
  status_b=$?

  [ "$status_a" -eq 0 ]
  [ "$status_b" -eq 0 ]
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
