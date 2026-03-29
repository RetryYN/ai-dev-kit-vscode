#!/bin/bash
set -eo pipefail
# 検証: helix-sprint が .1a→.5→completed のフル周回を正しく管理するか
# 受入条件: reset→6回next→completed、status で全ステップ completed 表示

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== 003: helix-sprint ==="

# reset
$CLI/helix-sprint reset >/dev/null 2>&1

# .1a start
out=$($CLI/helix-sprint next 2>&1)
echo "$out" | grep -q ".1a" || { echo "FAIL: start .1a"; exit 1; }

# full cycle: .1a→.1b→.2→.3→.4→.5→completed
for i in 1 2 3 4 5; do
  $CLI/helix-sprint next >/dev/null 2>&1
done

# verify completed
out=$($CLI/helix-sprint status 2>&1)
echo "$out" | grep -q "Sprint 完了" || echo "$out" | grep -q "completed" || { echo "FAIL: not completed"; exit 1; }

echo "PASS"
