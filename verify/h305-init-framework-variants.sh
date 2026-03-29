#!/bin/bash
set -eo pipefail
# H305: Python/Go/Rust フレームワーク検出

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
echo "=== H305: Init Framework Variants ==="

test_framework() {
  local marker="$1" expected="$2" label="$3"
  local D=$(mktemp -d /tmp/helix-verify-XXXXXX)
  cd "$D" && git init -q && git config user.email "t@t" && git config user.name "T"
  echo "t" > README.md && echo "" > "$marker" && git add . && git commit -q -m "i"
  HELIX_PROJECT_ROOT="$D" $CLI/helix-init --project-name t --force >/dev/null 2>&1
  if grep -q "$expected" "$D/.helix/gate-checks.yaml" 2>/dev/null; then
    rm -rf "$D"
    return 0
  else
    echo "FAIL: $label — expected '$expected' in gate-checks.yaml"
    rm -rf "$D"
    return 1
  fi
}

test_framework "pyproject.toml" "mypy" "Python" || exit 1
test_framework "go.mod" "go vet" "Go" || exit 1
test_framework "Cargo.toml" "cargo check" "Rust" || exit 1

echo "PASS: Python/Go/Rust all detected"
