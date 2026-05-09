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
