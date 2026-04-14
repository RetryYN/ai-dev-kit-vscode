#!/bin/bash
set -euo pipefail

# HELIX 全ツール一発セットアップ
# Usage: bash ~/ai-dev-kit-vscode/cli/scripts/setup-all.sh [--skip-optional]

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
SCRIPTS="$HELIX_HOME/cli/scripts"
SKIP_OPTIONAL=false
[[ "${1:-}" == "--skip-optional" ]] && SKIP_OPTIONAL=true

echo "================================================"
echo "  HELIX 全ツール一発セットアップ"
echo "================================================"
echo ""

# 1. HELIX 本体セットアップ
echo "[1/6] HELIX 本体..."
bash "$HELIX_HOME/setup.sh" 2>&1 | tail -3
echo ""

# 2. プロジェクト初期化（.helix/ がなければ）
if [[ ! -d ".helix" ]]; then
  echo "[2/6] プロジェクト初期化..."
  "$HELIX_HOME/cli/helix-init" --project-name "$(basename "$(pwd)")" 2>&1 | tail -5
else
  echo "[2/6] プロジェクト初期化... スキップ（既存）"
fi
echo ""

# 3. 環境チェック
echo "[3/6] 環境チェック..."
"$HELIX_HOME/cli/helix-doctor" 2>&1 | tail -5
echo ""

if [[ "$SKIP_OPTIONAL" == true ]]; then
  echo "[4-6] オプショナルツール... スキップ（--skip-optional）"
  echo ""
  echo "================================================"
  echo "  セットアップ完了！"
  echo "================================================"
  echo ""
  echo "次のステップ:"
  echo "  helix size --files N --lines N --type TYPE --drive DRIVE"
  echo "  helix matrix add-feature <name> --drive <type>"
  echo "  helix status"
  exit 0
fi

# 4. テキスト品質ツール
echo "[4/6] テキスト品質ツール..."
if command -v npm >/dev/null 2>&1; then
  bash "$SCRIPTS/setup-textlint.sh" 2>&1 | tail -2
else
  echo "  スキップ（npm なし）"
fi
echo ""

# 5. テスト・検証ツール
echo "[5/6] テスト・検証ツール..."
if command -v npm >/dev/null 2>&1; then
  bash "$SCRIPTS/setup-playwright.sh" 2>&1 | tail -2
  bash "$SCRIPTS/setup-axe.sh" 2>&1 | tail -2
else
  echo "  スキップ（npm なし）"
fi
echo ""

# 6. ドキュメント・図表ツール
echo "[6/6] ドキュメント・図表ツール..."
if command -v npm >/dev/null 2>&1; then
  bash "$SCRIPTS/setup-marp.sh" 2>&1 | tail -2
fi
bash "$SCRIPTS/setup-d2.sh" 2>&1 | tail -2 || echo "  D2: スキップ"
echo ""

echo "================================================"
echo "  HELIX 全ツール セットアップ完了！"
echo "================================================"
echo ""
echo "次のステップ:"
echo "  helix size --files N --lines N --type TYPE --drive DRIVE"
echo "  helix matrix add-feature <name> --drive <type>"
echo "  helix status"
