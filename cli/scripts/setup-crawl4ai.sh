#!/bin/bash
set -euo pipefail

case "${1:-}" in
  --help|-h)
    echo "使い方: setup-crawl4ai.sh"
    echo ""
    echo "Crawl4AI をインストールします。"
    exit 0
    ;;
esac

echo "=== Crawl4AI セットアップ ==="
pip install crawl4ai
echo "完了: Crawl4AI をインストールしました"
echo "使い方: python3 -c 'from crawl4ai import AsyncWebCrawler; ...'"
echo ""
echo "MCP サーバー: pip install crawl4ai-mcp-server"
