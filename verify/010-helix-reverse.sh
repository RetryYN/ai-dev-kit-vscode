#!/bin/bash
set -eo pipefail
# 検証: helix-reverse が前提条件チェックと dry-run を正しく処理するか
# 受入条件: R0 dry-run → OK、R1 prereq fail（RG0未通過）

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== 010: helix-reverse ==="

# status
out=$($CLI/helix-reverse status 2>&1)
echo "$out" | grep -q "Reverse" || { echo "FAIL: status"; exit 1; }

# R0 dry-run
out=$($CLI/helix-reverse R0 --dry-run 2>&1)
echo "$out" | grep -q "Evidence" || { echo "FAIL: R0 dry-run"; exit 1; }

# R1 prereq fail
set +e
out=$($CLI/helix-reverse R1 --dry-run 2>&1)
exit_code=$?
set -e
[[ $exit_code -ne 0 ]] || { echo "FAIL: R1 should fail prereq"; exit 1; }

echo "PASS"
