#!/bin/bash
set -eo pipefail
# H306: 全 type パターンのフェーズスキップ

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
echo "=== H306: Size All Type Patterns ==="

check_phases() {
  local args="$1" expected="$2" label="$3"
  set +e
  out=$(eval "$CLI/helix-size $args" 2>&1)
  set -e
  phases=$(echo "$out" | grep "推奨フェーズ" | sed 's/推奨フェーズ: //')
  if [[ "$phases" == *"$expected"* ]]; then
    return 0
  else
    echo "FAIL: $label — got '$phases', expected to contain '$expected'"
    return 1
  fi
}

# S patterns
check_phases "--files 1 --lines 10 --type bugfix" "L4" "S bugfix" || exit 1
check_phases "--files 1 --lines 10 --type refactor" "L4" "S refactor" || exit 1
check_phases "--files 1 --lines 10 --type doc" "L4" "S doc" || exit 1
check_phases "--files 2 --lines 50 --ui --type ui-change" "L5" "S ui-change has L5" || exit 1
check_phases "--files 2 --lines 50 --type new-feature" "L2" "S new-feature has L2" || exit 1

# M patterns
check_phases "--files 5 --lines 200 --type new-module --api" "L1" "M new-module has L1" || exit 1

echo "PASS: all type patterns correct"
