#!/bin/bash
set -euo pipefail
echo "=== Playwright セットアップ ==="
npm init -y 2>/dev/null || true
npm install --save-dev @playwright/test
npx playwright install chromium
echo "完了: Playwright + Chromium をインストールしました"
echo "記録: npx playwright codegen <url>"
echo "実行: npx playwright test"
