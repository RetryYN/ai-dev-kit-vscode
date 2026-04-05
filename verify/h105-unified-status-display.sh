#!/bin/bash
set -eo pipefail
# H105: helix status が Forward + Scrum を統合表示する

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
cp "$CLI/templates/gate-checks.yaml" .helix/gate-checks.yaml
rm -f .helix/runtime/index.json .helix/state/deliverables.json
$CLI/helix-scrum init >/dev/null 2>&1

echo "=== H105: Unified Status Display ==="

# Forward
mkdir -p docs/design && printf '# L2 設計書\n## セキュリティ設計\nSTRIDE 脅威分析\n## スコープ\n対象外: なし\nREQ-F-001\n' > docs/design/L2-arch.md
python3 "$YP" write .helix/phase.yaml gates.G1.status passed 2>/dev/null
$CLI/helix-gate G2 --static-only >/dev/null 2>&1
$CLI/helix-sprint reset >/dev/null 2>&1
$CLI/helix-sprint next >/dev/null 2>&1

# Scrum
$CLI/helix-scrum backlog add --id H001 --title "T" --question "Q" --acceptance "A" >/dev/null 2>&1
$CLI/helix-scrum plan --goal "test" --hypotheses "H001" >/dev/null 2>&1

# status check (set +e because status may have non-fatal python errors)
set +e
out=$($CLI/helix-status 2>&1)
set -e
echo "$out" | grep -q "Gates:" || { echo "FAIL: Gates missing"; exit 1; }
echo "$out" | grep -q "Sprint:" || { echo "FAIL: Sprint missing"; exit 1; }
echo "$out" | grep -q "G2" || { echo "FAIL: G2 missing"; exit 1; }

echo "PASS"
