#!/bin/bash
set -eo pipefail
# 検証: ADR ファイル作成時に index.md が自動再生成されるか
# 受入条件: ADR-001.md 作成 → index.md にタイトルとステータスが含まれる

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== 007: adr-index ==="

mkdir -p docs/adr
cat > docs/adr/ADR-001.md << 'EOF'
# ADR-001: 認証方式の選定

## ステータス: 承認済み（2026-03-30）
EOF

$CLI/helix-hook "$DIR/docs/adr/ADR-001.md" >/dev/null 2>&1

[[ -f docs/adr/index.md ]] || { echo "FAIL: index.md not created"; exit 1; }
grep -q "ADR-001" docs/adr/index.md || { echo "FAIL: ADR-001 not in index"; exit 1; }

echo "PASS"
