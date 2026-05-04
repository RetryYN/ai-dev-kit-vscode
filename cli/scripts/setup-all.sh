#!/bin/bash
set -euo pipefail

# HELIX 全ツール一発セットアップ
# Usage: bash ~/ai-dev-kit-vscode/cli/scripts/setup-all.sh [--yes] [--skip-packages]

HELIX_HOME="${HELIX_HOME:-$HOME/ai-dev-kit-vscode}"
SCRIPTS="$HELIX_HOME/cli/scripts"
SKIP_OPTIONAL=false
YES=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes)
      YES=true
      shift
      ;;
    --skip-optional|--skip-packages)
      SKIP_OPTIONAL=true
      shift
      ;;
    --help|-h)
      echo "使い方: setup-all.sh [--yes] [--skip-packages]"
      echo ""
      echo "HELIX 本体 setup と project bootstrap を実行します。"
      echo "開発支援パッケージの実インストールは --yes 指定時のみ行います。"
      exit 0
      ;;
    *)
      echo "エラー: 不明なオプション: $1" >&2
      exit 2
      ;;
  esac
done

echo "================================================"
echo "  HELIX 全ツール一発セットアップ"
echo "================================================"
echo ""

# 1. HELIX 本体セットアップ
echo "[1/6] HELIX 本体..."
bash "$HELIX_HOME/setup.sh" 2>&1 | tail -3
echo ""

# 2. プロジェクト bootstrap
echo "[2/6] プロジェクト bootstrap..."
"$HELIX_HOME/cli/helix" setup bootstrap --project-name "$(basename "$(pwd)")" 2>&1 | tail -8
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
if [[ "$YES" == true ]]; then
  "$HELIX_HOME/cli/helix" setup packages install --name textlint --yes 2>&1 | tail -4
else
  "$HELIX_HOME/cli/helix" setup packages install --name textlint 2>&1 | tail -4
fi
echo ""

# 5. テスト・検証ツール
echo "[5/6] テスト・検証ツール..."
if [[ "$YES" == true ]]; then
  "$HELIX_HOME/cli/helix" setup packages install --name playwright --yes 2>&1 | tail -4
  "$HELIX_HOME/cli/helix" setup packages install --name axe --yes 2>&1 | tail -4
else
  "$HELIX_HOME/cli/helix" setup packages install --name playwright 2>&1 | tail -4
  "$HELIX_HOME/cli/helix" setup packages install --name axe 2>&1 | tail -4
fi
echo ""

# 6. ドキュメント・図表ツール
echo "[6/6] ドキュメント・図表ツール..."
if [[ "$YES" == true ]]; then
  "$HELIX_HOME/cli/helix" setup packages install --name marp --yes 2>&1 | tail -4
  "$HELIX_HOME/cli/helix" setup packages install --name d2 --yes 2>&1 | tail -4 || echo "  D2: スキップ"
else
  "$HELIX_HOME/cli/helix" setup packages install --name marp 2>&1 | tail -4
  "$HELIX_HOME/cli/helix" setup packages install --name d2 2>&1 | tail -4
fi
echo ""

echo "================================================"
echo "  HELIX 全ツール セットアップ完了！"
echo "================================================"
echo ""
echo "次のステップ:"
if [[ "$YES" != true && "$SKIP_OPTIONAL" != true ]]; then
  echo "  開発支援パッケージを実インストールする場合: bash $SCRIPTS/setup-all.sh --yes"
fi
echo "  helix size --files N --lines N --type TYPE --drive DRIVE"
echo "  helix matrix add-feature <name> --drive <type>"
echo "  helix status"
