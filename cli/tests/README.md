# HELIX bats テスト実行手順

## 1. bats セットアップ（Linux/WSL）

```bash
bash cli/scripts/setup-bats.sh
```

`apt-get` + 権限あり環境では `bats` をインストールします。  
権限なし/オフライン環境では `~/.local/bin/bats` に `bats-lite` を配置します。

必要なら PATH を追加してください。

```bash
export PATH="$HOME/.local/bin:$PATH"
```

`~/.local/bin` に書き込めない環境では `BATS_BIN_DIR` を指定できます。

```bash
BATS_BIN_DIR=/tmp/helix-bats-bin bash cli/scripts/setup-bats.sh
export PATH="/tmp/helix-bats-bin:$PATH"
```

## 2. bats 実行

```bash
bats cli/tests/*.bats
```

## 3. helix-test 統合実行

```bash
helix test
```

`helix test` の最終サマリに bats の結果（passed/failed/skipped）が表示されます。
