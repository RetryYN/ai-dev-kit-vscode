#!/bin/bash
set -eo pipefail
# H310: .helix/ なしプロジェクトでの no-op

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
# .helix/ を作らない

echo "=== H310: No Helix Dir Noop ==="

# hook → exit 0, no output
set +e
out=$($CLI/helix-hook "$DIR/somefile.ts" 2>&1)
r=$?
set -e
[[ $r -eq 0 ]] || { echo "FAIL: hook should exit 0 (got $r)"; exit 1; }
[[ -z "$out" ]] || { echo "FAIL: hook should be silent"; exit 1; }

# sprint → error message
set +e
out=$($CLI/helix-sprint status 2>&1)
r=$?
set -e
[[ $r -ne 0 ]] || { echo "FAIL: sprint should fail without .helix"; exit 1; }

# status → error message
set +e
out=$($CLI/helix-status 2>&1)
r=$?
set -e
[[ $r -ne 0 ]] || { echo "FAIL: status should fail without .helix"; exit 1; }

echo "PASS: hook=noop, sprint=error, status=error"
