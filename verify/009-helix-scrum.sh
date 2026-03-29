#!/bin/bash
set -eo pipefail
# 検証: helix-scrum のフルフロー（init→backlog→plan→verify→decide）が動作するか
# 受入条件: 仮説追加→スプリント開始→検証実行→判定→状態正しい

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== 009: helix-scrum ==="

# init
$CLI/helix-scrum init >/dev/null 2>&1
[[ -f .helix/scrum/backlog.yaml ]] || { echo "FAIL: backlog not created"; exit 1; }

# backlog add
$CLI/helix-scrum backlog add --id H001 --title "Test" --question "Q" --acceptance "A" >/dev/null 2>&1
out=$($CLI/helix-scrum backlog list 2>&1)
echo "$out" | grep -q "H001" || { echo "FAIL: H001 not in backlog"; exit 1; }

# verify script created
[[ -f verify/h001-test.sh ]] || { echo "FAIL: verify script not created"; exit 1; }

# plan
$CLI/helix-scrum plan --goal "Test" --hypotheses "H001" >/dev/null 2>&1

# verify (should fail — script is skeleton)
set +e
$CLI/helix-scrum verify >/dev/null 2>&1
vresult=$?
set -e
[[ $vresult -eq 1 ]] || { echo "FAIL: verify should fail on skeleton"; exit 1; }

# make verify pass
echo '#!/bin/bash' > verify/h001-test.sh
echo 'echo "PASS"; exit 0' >> verify/h001-test.sh
chmod +x verify/h001-test.sh

set +e
$CLI/helix-scrum verify >/dev/null 2>&1
vresult=$?
set -e
[[ $vresult -eq 0 ]] || { echo "FAIL: verify should pass now"; exit 1; }

# decide
out=$($CLI/helix-scrum decide --hypothesis H001 --confirmed 2>&1)
echo "$out" | grep -q "confirmed" || { echo "FAIL: decide not confirmed"; exit 1; }

# status
out=$($CLI/helix-scrum status 2>&1)
echo "$out" | grep -q "Sprint" || { echo "FAIL: status missing sprint"; exit 1; }

echo "PASS"
