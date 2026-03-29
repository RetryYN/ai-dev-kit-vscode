#!/bin/bash
set -eo pipefail
# H309: 空/破損 YAML で graceful failure

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
mkdir -p .helix

echo "=== H309: Graceful YAML Failure ==="

# 空の phase.yaml
touch .helix/phase.yaml
set +e
out=$($CLI/helix-status 2>&1)
r=$?
set -e
# クラッシュ（Python stack trace）がないこと
echo "$out" | grep -qv "Traceback" || { echo "FAIL: stack trace on empty yaml"; exit 1; }

# 破損 YAML
echo "{{{{invalid yaml" > .helix/phase.yaml
set +e
out=$($CLI/helix-sprint status 2>&1)
r=$?
set -e
echo "$out" | grep -qv "Traceback" || { echo "FAIL: stack trace on corrupt yaml"; exit 1; }

echo "PASS: no stack traces on empty/corrupt YAML"
