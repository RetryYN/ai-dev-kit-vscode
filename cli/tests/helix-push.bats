#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  REAL_PYTHON3="$(command -v python3)"

  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  ORIGIN_DIR="$TMP_ROOT/origin.git"
  SEED_DIR="$TMP_ROOT/seed"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  mkdir -p "$HOME_DIR" "$BIN_DIR"

  git init --bare "$ORIGIN_DIR" >/dev/null 2>&1
  git init -b main "$SEED_DIR" >/dev/null 2>&1
  git -C "$SEED_DIR" config user.email "qa@example.com"
  git -C "$SEED_DIR" config user.name "QA"
  printf '# seed\n' > "$SEED_DIR/README.md"
  git -C "$SEED_DIR" add README.md
  git -C "$SEED_DIR" commit -q -m "init"
  git -C "$SEED_DIR" remote add origin "$ORIGIN_DIR"
  git -C "$SEED_DIR" push -q -u origin main
  git --git-dir="$ORIGIN_DIR" symbolic-ref HEAD refs/heads/main
  git clone -q "$ORIGIN_DIR" "$PROJECT_ROOT"
  git -C "$PROJECT_ROOT" config user.email "qa@example.com"
  git -C "$PROJECT_ROOT" config user.name "QA"
  mkdir -p "$PROJECT_ROOT/cli/tests"
  : > "$PROJECT_ROOT/cli/tests/sample.bats"

  cat > "$BIN_DIR/python3" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == "-m" && "\$2" == "pytest" && "\$3" == "cli/lib/tests/" && "\$4" == "-q" ]]; then
  if [[ "\${HELIX_PUSH_PYTEST_STATUS:-0}" -ne 0 ]]; then
    echo "pytest failed" >&2
    exit "\${HELIX_PUSH_PYTEST_STATUS}"
  fi
  echo "1147 passed in 1.23s"
  exit 0
fi
if [[ "\$1" == "-m" && "\$2" == "pytest" && "\$3" == "cli/lib/tests/test_command_catalog.py" && "\$4" == "-q" ]]; then
  if [[ "\${HELIX_PUSH_CATALOG_STATUS:-0}" -ne 0 ]]; then
    echo "missing routed command 'X'" >&2
    exit "\${HELIX_PUSH_CATALOG_STATUS}"
  fi
  echo "4 passed in 0.02s"
  exit 0
fi
exec "$REAL_PYTHON3" "\$@"
EOF
  cat > "$BIN_DIR/bats" <<'EOF'
#!/usr/bin/env bash
if [[ "${HELIX_PUSH_BATS_STATUS:-0}" -ne 0 ]]; then
  echo "bats failed" >&2
  exit "${HELIX_PUSH_BATS_STATUS}"
fi
echo "1..452"
EOF
  cat > "$BIN_DIR/pre-commit" <<'EOF'
#!/usr/bin/env bash
if [[ "${HELIX_PUSH_SECRET_STATUS:-0}" -ne 0 ]]; then
  echo "secret detected" >&2
  exit "${HELIX_PUSH_SECRET_STATUS}"
fi
echo "Passed"
EOF
  chmod +x "$BIN_DIR/python3" "$BIN_DIR/bats" "$BIN_DIR/pre-commit"

  export PATH="$BIN_DIR:$PATH"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

create_commit() {
  local file_name="${1:-feature.txt}"
  printf 'change\n' >> "$PROJECT_ROOT/$file_name"
  git -C "$PROJECT_ROOT" add "$file_name"
  git -C "$PROJECT_ROOT" commit -q -m $'feature\n\nCo-Authored-By: QA <qa@example.com>'
}

origin_main_sha() {
  git --git-dir="$ORIGIN_DIR" rev-parse refs/heads/main
}

@test "test_push_gate_dry_run_succeeds_when_clean" {
  create_commit

  run "$HELIX_ROOT/cli/helix-push" --gate
  [ "$status" -eq 0 ]
  [[ "$output" == *"[helix push] gate verification..."* ]]
  [[ "$output" == *"✓ G-tests"* ]]
  [[ "$output" == *"✓ G-catalog"* ]]
  [[ "$output" == *"✓ G-secret"* ]]
  [[ "$output" == *"✓ G-ff"* ]]
  [[ "$output" == *"✓ G-attr"* ]]
  [[ "$output" == *"✓ G-nondestructive"* ]]
  [[ "$output" == *"[helix push] all gates PASS"* ]]
}

@test "test_push_gate_fail_blocks_execute" {
  create_commit blocked.txt
  before_local="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
  before_origin="$(origin_main_sha)"

  run env HELIX_PUSH_SECRET_STATUS=1 "$HELIX_ROOT/cli/helix-push" --gate --execute
  [ "$status" -eq 1 ]
  [[ "$output" == *"✗ G-secret"* ]]
  [[ "$output" == *"Fix: secret detected、staged change を確認"* ]]
  [[ "$output" == *"[helix push] BLOCKED (1 gate failed)"* ]]
  [ "$(git -C "$PROJECT_ROOT" rev-parse HEAD)" = "$before_local" ]
  [ "$(origin_main_sha)" = "$before_origin" ]
}

@test "test_push_help_documents_options" {
  run "$HELIX_ROOT/cli/helix-push" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"使い方: helix push --gate"* ]]
  [[ "$output" == *"--execute"* ]]
  [[ "$output" == *"--remote REMOTE"* ]]
  [[ "$output" == *"--branch BRANCH"* ]]
}

@test "test_push_invalid_option_errors" {
  run "$HELIX_ROOT/cli/helix-push" --nope
  [ "$status" -eq 2 ]
  [[ "$output" == *"不明なオプションです: --nope"* ]]
}

@test "test_push_execute_calls_git_push" {
  create_commit execute.txt
  local_head="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"

  run "$HELIX_ROOT/cli/helix-push" --gate --execute --remote origin --branch main
  [ "$status" -eq 0 ]
  [[ "$output" == *"[helix push] all gates PASS -> executing git push origin main"* ]]
  [ "$(origin_main_sha)" = "$local_head" ]
}
