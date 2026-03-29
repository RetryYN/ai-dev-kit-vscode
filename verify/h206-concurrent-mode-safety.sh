#!/bin/bash
set -eo pipefail
# H206: Forward + Scrum 並行運用で phase.yaml が壊れないか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "init"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
$CLI/helix-scrum init >/dev/null 2>&1

echo "=== H206: Concurrent Mode Safety ==="

# Forward: ゲート操作
mkdir -p docs/design && echo "# L2" > docs/design/L2-arch.md
$CLI/helix-gate G2 --static-only >/dev/null 2>&1

# Scrum: バックログ + スプリント操作
$CLI/helix-scrum backlog add --id H001 --title "T" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum plan --goal "test" --hypotheses "H001" >/dev/null 2>&1

# Forward: スプリント操作
$CLI/helix-sprint reset >/dev/null 2>&1
$CLI/helix-sprint next >/dev/null 2>&1

# 全セクションが壊れていないか確認
g2=$(python3 "$YP" read .helix/phase.yaml gates.G2.status 2>/dev/null)
[[ "$g2" == "passed" ]] || { echo "FAIL: G2 corrupted ($g2)"; exit 1; }

sprint=$(python3 "$YP" read .helix/phase.yaml sprint.current_step 2>/dev/null)
[[ "$sprint" == ".1a" ]] || { echo "FAIL: sprint corrupted ($sprint)"; exit 1; }

# phase.yaml が valid な YAML のままか
python3 "$YP" dump .helix/phase.yaml | python3 -c "import sys,json; json.load(sys.stdin)" || { echo "FAIL: phase.yaml corrupted"; exit 1; }

# Scrum backlog が壊れていないか
out=$($CLI/helix-scrum backlog list 2>&1)
echo "$out" | grep -q "H001" || { echo "FAIL: scrum backlog corrupted"; exit 1; }

# 追加の Forward 操作後もまだ OK か
$CLI/helix-sprint next >/dev/null 2>&1
sprint2=$(python3 "$YP" read .helix/phase.yaml sprint.current_step 2>/dev/null)
[[ "$sprint2" == ".1b" ]] || { echo "FAIL: sprint advance corrupted ($sprint2)"; exit 1; }

# gate も変わっていないか
g2_after=$(python3 "$YP" read .helix/phase.yaml gates.G2.status 2>/dev/null)
[[ "$g2_after" == "passed" ]] || { echo "FAIL: G2 changed after sprint op ($g2_after)"; exit 1; }

echo "PASS: Forward(gates+sprint) + Scrum(backlog+plan) coexist safely"
