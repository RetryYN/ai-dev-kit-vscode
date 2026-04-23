#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  HELIX_GATE="$HELIX_ROOT/cli/helix-gate"
  YAML_PARSER="$HELIX_ROOT/cli/lib/yaml_parser.py"

  TMP_ROOT="$(mktemp -d)"
  PROJECT_ROOT="$TMP_ROOT/project"
  mkdir -p "$PROJECT_ROOT"
  cd "$PROJECT_ROOT"

  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"
  echo "init" > README.md
  git add README.md
  git commit -q -m "init"

  export HELIX_HOME="$HELIX_ROOT"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"

  "$HELIX_ROOT/cli/helix-init" --project-name g5-design-md-test >/dev/null 2>&1

  # Unrelated checks are disabled to isolate G5 design-md behavior.
  rm -f .helix/matrix.yaml .helix/runtime/index.json .helix/state/deliverables.json
  cat > .helix/gate-checks.yaml <<'YAML'
G5:
  name: "G5 design-md test"
  static:
  ai:
YAML

  MOCK_BIN="$TMP_ROOT/mock-bin"
  MIN_BIN="$TMP_ROOT/min-bin"
  mkdir -p "$MOCK_BIN" "$MIN_BIN"

  for cmd in python3 grep date dirname basename; do
    ln -s "$(command -v "$cmd")" "$MIN_BIN/$cmd"
  done
}

teardown() {
  rm -rf "$TMP_ROOT"
}

set_gate_context() {
  local drive="$1"
  local ui="$2"
  python3 "$YAML_PARSER" write .helix/phase.yaml "gates.G4.status" "passed" >/dev/null
  python3 "$YAML_PARSER" write .helix/phase.yaml "sprint.drive" "$drive" >/dev/null
  python3 "$YAML_PARSER" write .helix/phase.yaml "sprint.ui" "$ui" >/dev/null
}

write_design_md() {
  mkdir -p docs
  cat > docs/DESIGN.md <<'EOF'
---
colors:
  primary: "#1f6feb"
typography:
  body:
    family: "Noto Sans JP"
rounded:
  md: "8px"
spacing:
  md: "16px"
components:
  button:
    radius: "{rounded.md}"
---

# DESIGN.md

## Overview
## Colors
## Typography
## Layout
## Elevation
## Shapes
## Components
## Do's & Don'ts
EOF
}

mock_npx() {
  cat > "$MOCK_BIN/npx" <<'EOF'
#!/bin/bash
set -euo pipefail

if [[ -n "${NPX_MOCK_LOG:-}" ]]; then
  echo "$*" >> "$NPX_MOCK_LOG"
fi

args=("$@")
if [[ "${args[0]:-}" == "--yes" ]]; then
  args=("${args[@]:1}")
fi
cmd="${args[1]:-}"

case "${NPX_MOCK_MODE:-pass}" in
  pass)
    if [[ "$cmd" == "--version" ]]; then
      echo "0.1.1"
    else
      echo "info: lint passed"
      echo "warning: minor token suggestion"
    fi
    exit 0
    ;;
  lint_fail)
    echo "error: section-order" >&2
    exit 1
    ;;
  exec_fail)
    echo "npx fetch failed" >&2
    exit 127
    ;;
  *)
    exit 0
    ;;
esac
EOF
  chmod +x "$MOCK_BIN/npx"
}

@test "1 drive=fe + DESIGN.mdあり + lint exit 0 -> G5 PASS" {
  set_gate_context "fe" "true"
  write_design_md
  mock_npx

  run env PATH="$MOCK_BIN:/usr/bin:/bin" NPX_MOCK_MODE=pass \
    HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    "$HELIX_GATE" G5 --static-only

  [ "$status" -eq 0 ]
  [[ "$output" =~ "=== G5 PASS ===" ]]
  [[ "$output" =~ "[design-md][INFO]" ]]
}

@test "2 drive=fe + DESIGN.mdなし -> G5 FAIL (mandatory_fail)" {
  set_gate_context "fe" "true"
  mock_npx

  run env PATH="$MOCK_BIN:/usr/bin:/bin" NPX_MOCK_MODE=pass \
    HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    "$HELIX_GATE" G5 --static-only

  [ "$status" -eq 1 ]
  [[ "$output" =~ "missing required file: docs/DESIGN.md" ]]
  [[ "$output" =~ "=== G5 FAIL" ]]
}

@test "3 drive=fe + lint exit 1 -> G5 FAIL" {
  set_gate_context "fe" "true"
  write_design_md
  mock_npx

  run env PATH="$MOCK_BIN:/usr/bin:/bin" NPX_MOCK_MODE=lint_fail \
    HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    "$HELIX_GATE" G5 --static-only

  [ "$status" -eq 1 ]
  [[ "$output" =~ "lint failed for docs/DESIGN.md" ]]
  [[ "$output" =~ "=== G5 FAIL" ]]
}

@test "4 drive=be + ui=false -> auto-skip維持（lint未実行）" {
  set_gate_context "be" "false"
  mock_npx
  export NPX_MOCK_LOG="$TMP_ROOT/npx.log"

  run env PATH="$MOCK_BIN:/usr/bin:/bin" NPX_MOCK_MODE=pass NPX_MOCK_LOG="$NPX_MOCK_LOG" \
    HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    "$HELIX_GATE" G5 --static-only

  [ "$status" -eq 0 ]
  [[ "$output" =~ "auto-skipped" ]]
  [ ! -s "$NPX_MOCK_LOG" ]
}

@test "5 drive=be + ui=true + DESIGN.mdあり + lint exit 0 -> G5 PASS" {
  set_gate_context "be" "true"
  write_design_md
  mock_npx

  run env PATH="$MOCK_BIN:/usr/bin:/bin" NPX_MOCK_MODE=pass \
    HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    "$HELIX_GATE" G5 --static-only

  [ "$status" -eq 0 ]
  [[ "$output" =~ "=== G5 PASS ===" ]]
}

@test "6 drive=fullstack + npx利用不可 -> G5 FAIL (fail-close)" {
  set_gate_context "fullstack" "true"
  write_design_md

  run env PATH="$MIN_BIN" HELIX_HOME="$HELIX_ROOT" HELIX_PROJECT_ROOT="$PROJECT_ROOT" \
    "$HELIX_GATE" G5 --static-only

  [ "$status" -eq 1 ]
  [[ "$output" =~ "npx command not found" ]]
  [[ "$output" =~ "=== G5 FAIL" ]]
}
