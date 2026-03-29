#!/bin/bash
set -eo pipefail
# H308: Scrum の rejected/pivot 挙動

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT
cd "$DIR" && git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
$CLI/helix-scrum init >/dev/null 2>&1

echo "=== H308: Scrum Rejected and Pivot ==="

$CLI/helix-scrum backlog add --id H001 --title "Reject" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum backlog add --id H002 --title "Pivot" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum plan --goal "test" --hypotheses "H001,H002" >/dev/null 2>&1

# rejected
out=$($CLI/helix-scrum decide --hypothesis H001 --rejected --learnings "did not work" 2>&1)
echo "$out" | grep -q "rejected" || { echo "FAIL: rejected message"; exit 1; }

# pivot
out=$($CLI/helix-scrum decide --hypothesis H002 --pivot --learnings "need different approach" 2>&1)
echo "$out" | grep -q "pivot" || { echo "FAIL: pivot message"; exit 1; }

# backlog list shows status
out=$($CLI/helix-scrum backlog list 2>&1)
echo "$out" | grep "H001" | grep -q "rejected" || { echo "FAIL: H001 not rejected in list"; exit 1; }
echo "$out" | grep "H002" | grep -q "pivot" || { echo "FAIL: H002 not pivot in list"; exit 1; }

echo "PASS: rejected + pivot both reflected"
