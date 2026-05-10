# Codex Test Bootstrap

`cli/helix-test` は依存不足を自動インストールしません。Codex 委譲環境では `HELIX_CODEX_INTERNAL=1` のときだけ warning を出し、手動 bootstrap をこの runbook に寄せます。

## Minimal Install

`bats` は次のいずれかで最小導入します。

- Ubuntu / Debian: `sudo apt-get update && sudo apt-get install -y bats`
- macOS (Homebrew): `brew install bats-core`
- Node.js 環境: `npm install -g bats`

`pytest` は次のいずれかで導入します。

- 既存 Python へ追加: `python3 -m pip install pytest`
- 仮想環境を使う場合: `python3 -m venv .venv && . .venv/bin/activate && python -m pip install -U pip pytest`

## PATH / Env Confirm

- `which bats`
- `which pytest`
- `python3 -c "import pytest; print(pytest.__file__)"`
- 必要なら `export PATH="$HOME/.local/bin:$PATH"` や仮想環境の `activate` を再実行します。

## Re-run Confirm

1. `which bats` と `which pytest` が解決することを確認する。
2. `HELIX_CODEX_INTERNAL=1 cli/helix-test` を再実行する。
3. warning が消え、通常の shell / bats / pytest 集計に戻ることを確認する。

## Why No Auto Install

- 実行中セッションの PATH や仮想環境を書き換えると、別タスクへ副作用が波及するため。
- `apt` / `brew` / `npm` / `pip` のどれが正解かは環境ごとに異なり、誤判定すると復旧コストが高いため。
- テストランナー自身が依存追加まで担うと、失敗原因の切り分けが難しくなるため。

## /tmp writable 確認 + TMPDIR 環境変数注入

Codex 委譲時に pytest が以下のエラーで停止する場合:

`FileNotFoundError: No usable temporary directory found`

これは Codex sandbox 内で `/tmp` への write が制約されているケースです。以下の手順で回避できます。

### 確認手順

```bash
# /tmp が writable か確認
helix codex --role pg --task 'touch /tmp/check && echo OK || echo NO' --dry-run
```

### 回避手順 (TMPDIR 注入)

helix codex 実行前に環境変数を設定します。

```bash
export TMPDIR="$HOME/.cache/helix-tmp"
mkdir -p "$TMPDIR"
helix codex --role pg --task '...' --approved --consent approved
```

または HELIX_CODEX env へ直接注入します（`cli/helix-codex` で対応済みの場合）。

```bash
HELIX_CODEX_ENV='TMPDIR=$HOME/.cache/helix-tmp' helix codex --role pg --task '...'
```

### 関連 PLAN

- PLAN-041 W-4: codex-test-bootstrap 起票 (bats / pytest 不在時 warning)
- PLAN-042 W-23: pytest /tmp 制約事象を実観測
- PLAN-043 W-1.C: 本拡張 (TMPDIR 注入手順)

## helix code find の前提

`helix code find` および関連コマンド (`helix code build`, `helix code stats`, etc.) は SQLite cache (`.helix/cache/code-catalog/`) を作成・読み書きするため、**writable な `.helix/` ディレクトリが必要** です。

read-only sandbox 環境 (codex-test など) では SQLite 接続失敗で OperationalError になります。代替手段:

- read-only env で実行する場合は `--no-cache` フラグ (もしあれば) を使う
- TMPDIR を writable path に設定し `HELIX_CACHE_DIR=$TMPDIR/helix-cache` を export
- 単純な grep で代替 (`rg "<keyword>" cli/`)
