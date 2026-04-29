#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$BIN_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
}

teardown() {
  rm -rf "$TMP_ROOT"
}

install_fake_gitleaks() {
  cat >"$BIN_DIR/gitleaks" <<'SH'
#!/usr/bin/env bash
echo "gitleaks version 8.99.0"
SH
  chmod +x "$BIN_DIR/gitleaks"
}

@test "helix audit preflight --verify-only succeeds when all components are ready" {
  install_fake_gitleaks
  PATH="$BIN_DIR:$PATH" "$HELIX_ROOT/cli/helix" setup install --name gitignore-helix >/dev/null
  PATH="$BIN_DIR:$PATH" "$HELIX_ROOT/cli/helix" setup install --name redaction-denylist >/dev/null

  run env PATH="$BIN_DIR:$PATH" "$HELIX_ROOT/cli/helix" audit preflight --verify-only
  [ "$status" -eq 0 ]
  [[ "$output" == *"PREFLIGHT OK (3/3 ready)"* ]]
  [[ "$output" == *"fail_closed_count: 0"* ]]
  [[ "$output" == *"### gitleaks"* ]]
  [[ "$output" == *"### gitignore-helix"* ]]
  [[ "$output" == *"### redaction-denylist"* ]]

  run bash -c "ls '$PROJECT_ROOT/.helix/audit/'preflight-*.log"
  [ "$status" -eq 0 ]

  run "$HELIX_ROOT/cli/helix" observe report --event audit.preflight.completed --format json
  [ "$status" -eq 0 ]
  [[ "$output" == *'"event_name": "audit.preflight.completed"'* ]]
  [[ "$output" == *'"fail_closed": 0'* ]]
}

@test "helix-audit preflight --verify-only reports fail-closed when components are missing" {
  run "$HELIX_ROOT/cli/helix-audit" preflight --verify-only
  [ "$status" -eq 1 ]
  [[ "$output" == *"PREFLIGHT FAILED:"* ]]
  [[ "$output" == *"component(s) need attention"* ]]
  [[ "$output" == *"fail_closed_count:"* ]]
  [[ "$output" == *"gitleaks is not installed"* ]]

  run bash -c "ls '$PROJECT_ROOT/.helix/audit/'preflight-*.log"
  [ "$status" -eq 0 ]
}
