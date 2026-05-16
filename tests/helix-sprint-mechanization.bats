#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  TOOL_HELPER="$HELIX_ROOT/cli/tests/_helix-bats-helper.bash"
  TMP_ROOT="$(mktemp -d)"
  source "$TOOL_HELPER"
  helix_bats_mark "$TMP_ROOT"

  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  BIN_DIR="$TMP_ROOT/bin"
  mkdir -p "$PROJECT_ROOT/.helix/reviews/plans" "$PROJECT_ROOT/tests" "$PROJECT_ROOT/src" "$HOME_DIR" "$BIN_DIR"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "bats@example.com"
  git config user.name "Bats"
  echo "seed" > README.md
  git add README.md
  git commit -q -m "init"

  cat > "$PROJECT_ROOT/.helix/phase.yaml" <<'EOF'
sprint:
  current_step: .3
EOF

  cat > "$PROJECT_ROOT/src/example.py" <<'EOF'
VALUE = 1
EOF

  cat > "$PROJECT_ROOT/tests/test_example.py" <<'EOF'
def test_example_passes():
    assert 1 + 1 == 2
EOF

  cat > "$PROJECT_ROOT/.helix/reviews/plans/PLAN-082.json" <<'EOF'
{"summary":"codex review approve"}
EOF

  cat > "$BIN_DIR/pytest" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${HELIX_FAKE_PYTEST_FAIL:-0}" == "1" ]]; then
  echo "1 failed in 0.01s"
  exit 1
fi
echo "1 passed in 0.01s"
EOF
  chmod +x "$BIN_DIR/pytest"

  export HELIX_HOME="$HELIX_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PATH="$BIN_DIR:$HELIX_ROOT/cli:$PATH"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  export HELIX_SPRINT_PYTEST_CMD="pytest"
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "I-CLI-001: helix sprint complete --auto-check --json が 4 種結果 dict を返す" {
  export HELIX_SPRINT_TARGET_FILES="$PROJECT_ROOT/src/example.py:$PROJECT_ROOT/tests/test_example.py"
  export HELIX_SPRINT_TEST_PATTERN="path:$PROJECT_ROOT/tests/test_example.py"

  run "$HELIX_ROOT/cli/helix-sprint" complete --auto-check --plan-id PLAN-082 --sprint .3 --skip-full-regression --json

  [ "$status" -eq 0 ]
  JSON_OUTPUT="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_OUTPUT"])
assert payload["plan_id"] == "PLAN-082", payload
assert payload["sprint"] == ".3", payload
assert payload["checks"]["py_compile"]["status"] == "pass", payload
assert payload["checks"]["relevant_tests"]["status"] == "pass", payload
assert payload["checks"]["full_regression"]["status"] == "skipped", payload
assert payload["checks"]["review"]["status"] == "pass", payload
assert payload["overall"] == "warn", payload
PY
}

@test "I-CLI-002: helix sprint addon security_audit が placeholder を返す" {
  run "$HELIX_ROOT/cli/helix-sprint" addon security_audit --plan-id PLAN-082

  [ "$status" -eq 0 ]
  [[ "$output" == *"addon placeholder: security_audit"* ]]
  [[ "$output" == *"PLAN-082"* ]]
  [[ "$output" == *"placeholder"* ]]
}

@test "I-CLI-003: helix sprint complete --auto-check --strict は py_compile fail で exit 1" {
  cat > "$PROJECT_ROOT/src/broken.py" <<'EOF'
def broken(:
    pass
EOF
  export HELIX_SPRINT_TARGET_FILES="$PROJECT_ROOT/src/broken.py"
  export HELIX_SPRINT_TEST_PATTERN="path:$PROJECT_ROOT/tests/test_example.py"

  run "$HELIX_ROOT/cli/helix-sprint" complete --auto-check --plan-id PLAN-082 --sprint .3 --skip-full-regression --strict --json

  [ "$status" -eq 1 ]
  JSON_OUTPUT="$output" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["JSON_OUTPUT"])
assert payload["overall"] == "fail", payload
assert payload["checks"]["py_compile"]["status"] == "fail", payload
PY
}
