#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR" "$PROJECT_ROOT/cli/config"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  git checkout -b main >/dev/null 2>&1
  cat > "$PROJECT_ROOT/cli/config/coding-rule-registry.yaml" <<'EOF'
entries:
  - id: CR-CODE-BASH
    rule: bash scripts stay mechanically linted
    sot_section: コーディング規約
    linter_tool:
      - bash_n
      - shellcheck
    enforcement:
      kind: ci_gate
      paths: []
      status: partial
  - id: CR-CODE-PY
    rule: python scripts stay mechanically linted
    sot_section: コーディング規約
    linter_tool:
      - py_compile
      - ruff
    enforcement:
      kind: ci_gate
      paths: []
      status: partial
EOF
  cat > "$PROJECT_ROOT/cli/config/coding-rule-registry-baseline.json" <<'EOF'
{
  "intentional_baseline": true,
  "owner": "codex",
  "created": "2026-06-14",
  "expiry": "2026-09-12",
  "generated_by": "bats",
  "reports": [
    {
      "check_name": "check_coding_rule_lint",
      "mode": "advisory",
      "findings": [],
      "metrics": {
        "finding_count": 0
      }
    }
  ]
}
EOF
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "helix doctor check_coding_rule_lint stays advisory by default" {
  cat > "$PROJECT_ROOT/bad.py" <<'EOF'
def broken(
    return 1
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" "$HELIX_ROOT/cli/helix-doctor" check_coding_rule_lint
  [ "$status" -eq 0 ]
  [[ "$output" == *"coding_rule_lint"* ]]
}

@test "helix doctor check_coding_rule_lint --gate fails on new changed-file violation" {
  cat > "$PROJECT_ROOT/bad.py" <<'EOF'
def broken(
    return 1
EOF

  run env HELIX_PROJECT_ROOT="$PROJECT_ROOT" HELIX_CHANGED_FILES="bad.py" "$HELIX_ROOT/cli/helix-doctor" check_coding_rule_lint --gate
  [ "$status" -eq 1 ]
  [[ "$output" == *"coding_rule_lint"* ]]
  [[ "$output" == *"new_findings=1"* ]]
}
