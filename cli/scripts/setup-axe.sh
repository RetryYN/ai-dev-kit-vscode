#!/bin/bash
set -eo pipefail

case "${1:-}" in
  --help|-h)
    echo "使い方: setup-axe.sh"
    echo ""
    echo "axe-core（CLI/Playwright）を開発依存としてインストールします。"
    exit 0
    ;;
esac

echo "=== axe-core セットアップ ==="
npm install --save-dev @axe-core/playwright @axe-core/cli
echo "完了: axe-core をインストールしました"
echo "CLI: npx @axe-core/cli <url>"
echo "Playwright: import AxeBuilder from '@axe-core/playwright'"
