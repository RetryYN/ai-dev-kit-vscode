#!/bin/bash
set -euo pipefail

case "${1:-}" in
  --help|-h)
    echo "使い方: setup-marp.sh"
    echo ""
    echo "Marp CLI を開発依存としてインストールします。"
    exit 0
    ;;
esac

echo "=== Marp CLI セットアップ ==="
npm install --save-dev @marp-team/marp-cli
echo "完了: Marp CLI をインストールしました"
echo "使い方: npx marp --pptx slides.md"
