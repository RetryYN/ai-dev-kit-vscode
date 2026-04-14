#!/bin/bash
set -euo pipefail
echo "=== textlint セットアップ ==="
npm init -y 2>/dev/null || true
npm install --save-dev \
  textlint \
  textlint-rule-preset-ja-technical-writing \
  @textlint-ja/textlint-rule-preset-ai-writing \
  textlint-rule-preset-jtf-style

cat > .textlintrc.json << 'EOF'
{
  "rules": {
    "preset-ja-technical-writing": true,
    "@textlint-ja/preset-ai-writing": true,
    "preset-jtf-style": true
  }
}
EOF
echo "完了: textlint + 3 プリセットをインストールしました"
echo "実行: npx textlint docs/**/*.md"
