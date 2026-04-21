#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BIN="${BATS_BIN_DIR:-$HOME/.local/bin}"
BATS_LITE="$SCRIPT_DIR/bats-lite"

echo "=== bats セットアップ ==="

if command -v bats >/dev/null 2>&1; then
  echo "既存 bats を利用します: $(command -v bats)"
  bats -v || bats --version || true
  exit 0
fi

if command -v apt-get >/dev/null 2>&1; then
  if [[ "$(id -u)" -eq 0 ]]; then
    echo "apt-get で bats をインストールします (root)"
    apt-get update
    apt-get install -y bats
  elif command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
    echo "sudo apt-get で bats をインストールします"
    sudo apt-get update
    sudo apt-get install -y bats
  else
    echo "apt-get は利用可能ですが権限がありません（sudo なし）。フォールバックに切り替えます。"
  fi
fi

if command -v bats >/dev/null 2>&1; then
  echo "bats インストール完了: $(command -v bats)"
  bats -v || bats --version || true
  exit 0
fi

if ! mkdir -p "$LOCAL_BIN" 2>/dev/null; then
  LOCAL_BIN="/tmp/helix-bats-bin"
  mkdir -p "$LOCAL_BIN"
fi
ln -sf "$BATS_LITE" "$LOCAL_BIN/bats"
chmod +x "$BATS_LITE" "$LOCAL_BIN/bats"

echo "フォールバック: bats-lite を $LOCAL_BIN/bats に配置しました。"
echo "PATH に $LOCAL_BIN が無い場合は以下を実行してください:"
echo "  export PATH=\"$LOCAL_BIN:\$PATH\""
"$LOCAL_BIN/bats" -v
