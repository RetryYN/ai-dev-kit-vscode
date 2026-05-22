#!/bin/bash
set -eo pipefail
# 検証: ADR index が frontmatter 優先で status/date を抽出し、本文 grep にもフォールバックするか
# 受入条件: frontmatter あり ADR は frontmatter 値を採用し、frontmatter なし ADR は本文から採用する

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
CLI="$HELIX_HOME/cli"
DIR=$(mktemp -d /tmp/helix-verify-XXXXXX)
trap 'rm -rf "$DIR"' EXIT

cd "$DIR"
git init -q && git config user.email "t@t" && git config user.name "T"
echo "t" > README.md && git add . && git commit -q -m "i"
export HELIX_PROJECT_ROOT="$DIR"
$CLI/helix-init --project-name t >/dev/null 2>&1

echo "=== 007b: adr-index-frontmatter ==="

mkdir -p docs/adr
cat > docs/adr/ADR-001.md << 'EOF'
---
status: Proposed
date: 2026-05-22
---
# ADR-001: Frontmatter 優先
EOF

cat > docs/adr/ADR-002.md << 'EOF'
# ADR-002: 本文フォールバック

## ステータス: 承認済み

2026-05-01
EOF

$CLI/helix-hook "$DIR/docs/adr/ADR-001.md" >/dev/null 2>&1
$CLI/helix-hook "$DIR/docs/adr/ADR-002.md" >/dev/null 2>&1

[[ -f docs/adr/index.md ]] || { echo "FAIL: index.md not created"; exit 1; }
grep -Fq "| ADR-001 | ADR-001: Frontmatter 優先 | Proposed | 2026-05-22 |" docs/adr/index.md || {
  echo "FAIL: ADR-001 frontmatter values not indexed"
  exit 1
}
grep -Fq "| ADR-002 | ADR-002: 本文フォールバック | 承認済み | 2026-05-01 |" docs/adr/index.md || {
  echo "FAIL: ADR-002 fallback values not indexed"
  exit 1
}

echo "PASS"
