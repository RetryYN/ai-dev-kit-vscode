#!/bin/bash
set -eo pipefail
# H303: Sprint edge cases

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== H303: Sprint Edge Cases ==="

# complete before start → error
set +e; out=$($CLI/helix-sprint complete 2>&1); r=$?; set -e
[[ $r -ne 0 ]] || { echo "FAIL: complete before start should fail"; exit 1; }

# reset → status shows not started
$CLI/helix-sprint reset >/dev/null 2>&1
out=$($CLI/helix-sprint status 2>&1)
echo "$out" | grep -q "未開始\|N/A\|null" || { echo "FAIL: reset status"; exit 1; }

# full cycle then next → already completed
$CLI/helix-sprint next >/dev/null 2>&1
for i in 1 2 3 4 5; do $CLI/helix-sprint next >/dev/null 2>&1; done
out=$($CLI/helix-sprint next 2>&1)
echo "$out" | grep -q "完了\|completed" || { echo "FAIL: next after completed"; exit 1; }

echo "PASS"
