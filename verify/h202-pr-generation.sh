#!/bin/bash
set -eo pipefail
# H202: helix-pr がゲート結果・コミット・テストプランを含むPRテンプレートを生成するか

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
YP="$CLI/lib/yaml_parser.py"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "init"
git branch -m master main 2>/dev/null || true
git checkout -b feature/test 2>/dev/null
echo "change" > src.txt && git add . && git commit -q -m "feat: add feature"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== H202: PR Generation ==="

# ゲート状態を設定
python3 "$YP" write .helix/phase.yaml gates.G2.status passed 2>/dev/null
python3 "$YP" write .helix/phase.yaml gates.G2.date 2026-03-30 2>/dev/null

# PR dry-run
set +e
out=$($CLI/helix-pr --dry-run --base main 2>&1)
set -e

echo "$out" | grep -q "Summary" || { echo "FAIL: Summary missing"; exit 1; }
echo "$out" | grep -q "Gate Results" || { echo "FAIL: Gate Results missing"; exit 1; }
echo "$out" | grep -q "Test Plan" || { echo "FAIL: Test Plan missing"; exit 1; }
echo "$out" | grep -q "G2" || { echo "FAIL: G2 not in gate table"; exit 1; }
echo "$out" | grep -q "feat: add feature" || { echo "FAIL: commit not in summary"; exit 1; }

echo "PASS"
