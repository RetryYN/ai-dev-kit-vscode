#!/bin/bash
set -eo pipefail

case "${1:-}" in
  --help|-h)
    echo "使い方: setup-d2.sh"
    echo ""
    echo "D2 をインストールします（brew または go が必要）。"
    exit 0
    ;;
esac

echo "=== D2 セットアップ ==="
if command -v brew >/dev/null 2>&1; then
  brew install d2
elif command -v go >/dev/null 2>&1; then
  go install oss.terrastruct.com/d2@latest
else
  echo "brew または go が必要です。https://d2lang.com/tour/install を参照してください。"
  exit 1
fi
echo "完了: D2 をインストールしました"
echo "使い方: d2 input.d2 output.svg"
