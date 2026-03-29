#!/bin/bash
set -eo pipefail
# H103: Scrum confirmed → Forward HELIX (size → sprint) handoff

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "init"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
$CLI/helix-scrum init >/dev/null 2>&1

echo "=== H103: Scrum → Forward Handoff ==="

$CLI/helix-scrum backlog add --id H001 --title "PoC" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum plan --goal "test" --hypotheses "H001" >/dev/null 2>&1
echo '#!/bin/bash' > verify/h001-poc.sh && echo 'exit 0' >> verify/h001-poc.sh && chmod +x verify/h001-poc.sh
$CLI/helix-scrum decide --hypothesis H001 --confirmed >/dev/null 2>&1

# Forward handoff
out=$($CLI/helix-size --files 3 --lines 80 --type new-feature 2>&1)
echo "$out" | grep -q "サイズ: S" || { echo "FAIL: size"; exit 1; }

$CLI/helix-sprint reset >/dev/null 2>&1
out=$($CLI/helix-sprint next 2>&1)
echo "$out" | grep -q ".1a" || { echo "FAIL: sprint start"; exit 1; }

echo "PASS"
