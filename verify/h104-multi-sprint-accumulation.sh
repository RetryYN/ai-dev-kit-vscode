#!/bin/bash
set -eo pipefail
# H104: Sprint 1 + Sprint 2 の検証スクリプトが蓄積して全実行される

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

echo "=== H104: Multi-sprint Accumulation ==="

# Sprint 1
$CLI/helix-scrum backlog add --id H001 --title "A" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum plan --goal "S1" --hypotheses "H001" >/dev/null 2>&1
echo '#!/bin/bash' > verify/h001-a.sh && echo 'echo A; exit 0' >> verify/h001-a.sh && chmod +x verify/h001-a.sh
$CLI/helix-scrum decide --hypothesis H001 --confirmed >/dev/null 2>&1
$CLI/helix-scrum review >/dev/null 2>&1

# Sprint 2
$CLI/helix-scrum backlog add --id H002 --title "B" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum plan --goal "S2" --hypotheses "H002" >/dev/null 2>&1
echo '#!/bin/bash' > verify/h002-b.sh && echo 'echo B; exit 0' >> verify/h002-b.sh && chmod +x verify/h002-b.sh

# verify で両方実行
out=$($CLI/helix-scrum verify 2>&1)
echo "$out" | grep -q "h001" || { echo "FAIL: S1 script missing"; exit 1; }
echo "$out" | grep -q "h002" || { echo "FAIL: S2 script missing"; exit 1; }
echo "$out" | grep -q "0 failed" || { echo "FAIL: not all passed"; exit 1; }

echo "PASS"
