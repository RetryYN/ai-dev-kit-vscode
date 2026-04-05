#!/bin/bash
set -eo pipefail
# 検証: helix-gate がゲート検証・前提条件チェック・ミニレトロを正しく実行するか
# 受入条件: G2 pass + retro 生成、G4 prereq fail（G3未通過）

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && echo '{"name":"t"}' > package.json
git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1
cp "$CLI/templates/gate-checks.yaml" .helix/gate-checks.yaml
rm -f .helix/runtime/index.json .helix/state/deliverables.json

echo "=== 004: helix-gate ==="

# G2: 設計書を作成して pass
mkdir -p docs/design && printf '# L2 設計書\n## セキュリティ設計\nSTRIDE 脅威分析\n## スコープ\n対象外: なし\nREQ-F-001\n' > docs/design/L2-arch.md
python3 "$YP" write .helix/phase.yaml gates.G1.status passed 2>/dev/null
out=$($CLI/helix-gate G2 --static-only 2>&1)
echo "$out" | grep -q "PASS" || { echo "FAIL: G2 should pass"; exit 1; }

# retro 生成確認
ls .helix/retros/*G2* >/dev/null 2>&1 || { echo "FAIL: retro not generated"; exit 1; }

# G4 prereq: G3 が pending なので fail
set +e
out=$($CLI/helix-gate G4 --static-only 2>&1)
exit_code=$?
set -e
[[ $exit_code -ne 0 ]] || { echo "FAIL: G4 should fail prereq"; exit 1; }
echo "$out" | grep -q "前提ゲート\|prereq" || { echo "FAIL: G4 prereq message"; exit 1; }

echo "PASS"
