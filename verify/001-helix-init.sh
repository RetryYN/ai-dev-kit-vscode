#!/bin/bash
set -eo pipefail
# 検証: helix-init がプロジェクトを正しく初期化するか
# 受入条件: .helix/, CLAUDE.md, .gitignore, docs/, agents/ が作成される。再実行で上書きしない。

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo '{"name":"t"}' > package.json && echo "t" > README.md
git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"

echo "=== 001: helix-init ==="

# 初回
$CLI/helix-init --project-name test-app >/dev/null 2>&1
[[ -d .helix ]] || { echo "FAIL: .helix/ not created"; exit 1; }
[[ -f .helix/phase.yaml ]] || { echo "FAIL: phase.yaml missing"; exit 1; }
[[ -f .helix/doc-map.yaml ]] || { echo "FAIL: doc-map.yaml missing"; exit 1; }
[[ -f .helix/gate-checks.yaml ]] || { echo "FAIL: gate-checks.yaml missing"; exit 1; }
[[ -f CLAUDE.md ]] || { echo "FAIL: CLAUDE.md missing"; exit 1; }
grep -q "CLAUDE.local.md" .gitignore || { echo "FAIL: .gitignore missing entry"; exit 1; }
[[ -d docs/design ]] || { echo "FAIL: docs/design/ missing"; exit 1; }
[[ -d docs/adr ]] || { echo "FAIL: docs/adr/ missing"; exit 1; }
[[ -d .claude/agents ]] || { echo "FAIL: .claude/agents/ missing"; exit 1; }
ls .claude/agents/fe-*.md >/dev/null 2>&1 || { echo "FAIL: FE agents missing"; exit 1; }

# 冪等性
output=$($CLI/helix-init --project-name test-app 2>&1)
echo "$output" | grep -q "skip" || { echo "FAIL: not idempotent"; exit 1; }

# フレームワーク検出
echo "$output" | grep -q "Node.js\|default" || { echo "FAIL: framework not detected"; exit 1; }

echo "PASS"
