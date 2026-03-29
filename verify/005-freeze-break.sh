#!/bin/bash
set -eo pipefail
# 検証: freeze-break が凍結違反を検出し、下流ゲートを invalidate するか
# 受入条件: G3 passed + src/api/ 変更 → WARN + G4 invalidated

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

echo "=== 005: freeze-break ==="

# G3 + G4 を passed にする
python3 "$YP" write .helix/phase.yaml gates.G3.status passed 2>/dev/null
python3 "$YP" write .helix/phase.yaml gates.G4.status passed 2>/dev/null

# API ファイルを変更
mkdir -p src/api && echo "test" > src/api/auth.ts

# hook を実行
set +e
out=$($CLI/helix-hook "$DIR/src/api/auth.ts" 2>&1)
set -e

echo "$out" | grep -q "API凍結違反" || { echo "FAIL: freeze-break not detected"; exit 1; }
echo "$out" | grep -q "下流ゲート無効化" || { echo "FAIL: cascade not triggered"; exit 1; }

# G4 が invalidated になったか
g4_status=$(python3 "$YP" read .helix/phase.yaml gates.G4.status 2>/dev/null)
[[ "$g4_status" == "invalidated" ]] || { echo "FAIL: G4 not invalidated (got: $g4_status)"; exit 1; }

echo "PASS"
