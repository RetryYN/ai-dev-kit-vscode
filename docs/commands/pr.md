# helix pr

## 概要

`helix pr` は、現在の branch から PR 本文を自動生成し、
必要に応じて gate 検証と `gh pr create` / `gh pr merge --squash` を連結する補助 CLI です。

用途は 2 系統あります。

- 既存モード: `phase.yaml` の gate 状態を確認しつつ、PR 本文 preview または PR 作成を行う
- gate モード: `cli/lib/push_gate.py` の 6 ゲート検証を実行し、PASS 時のみ PR 作成や auto-merge を進める

`gh` が利用可能な環境では PR 作成まで実行でき、`--dry-run` では書き込みなしで確認できます。

## 書式

```text
helix pr [--dry-run] [--gate] [--auto-merge] [--base BASE] [--title TITLE] [--body BODY] [--require-gates G4,G6] [--force]
```

代表例:

```bash
helix pr --dry-run
helix pr --gate
helix pr --gate --dry-run
helix pr --gate --auto-merge
helix pr --base release/2026-05 --title "release: May patch set"
helix pr --body "## Summary\nManual body"
```

## オプション

| オプション | 説明 |
| --- | --- |
| `--dry-run` | PR を作成せずに実行する。`--gate` なしでは PR preview、`--gate` ありでは gate 検証のみ |
| `--gate` | `cli/lib/push_gate.py` の 6 ゲート検証を実行してから PR 作成へ進む |
| `--auto-merge` | `--gate` 成功後に `gh pr merge --squash` を実行する。単独指定は入力エラー |
| `--base BASE` | PR の base branch。既定は `main` |
| `--title TITLE` | PR タイトルを明示指定する。未指定時は current branch 名を使う |
| `--body BODY` | PR 本文を明示指定する。未指定時は commit / release notes / diff stat から自動生成する |
| `--require-gates G4,G6` | 既存モードで確認する gate を明示指定する |
| `--force` | 既存モードで gate 未通過でも警告付きで継続する |
| `--help`, `-h` | ヘルプを表示する |

## 動作モード

### 1. preview モード

`--gate` を付けない場合の既存導線です。

- `.helix/matrix.yaml` から size を読み、既定 gate を決める
  - `S` は `G4`
  - それ以外は `G6`
- `.helix/phase.yaml` の gate 状態を確認する
- `--dry-run` なら PR preview を出力する
- `--dry-run` なしなら `gh pr create` を実行する

必要 gate が未通過なら exit code `1` で停止します。
`--force` を付けた場合だけ警告付きで継続します。

### 2. gate モード

`--gate` を付けると `cli/lib/push_gate.py` の `run_all_gates()` を再利用します。

- 6 ゲートを実行する
- すべて PASS した場合だけ PR 作成へ進む
- `--dry-run` を併用した場合は gate 検証だけ行い、PR は作らない
- `--auto-merge` を併用した場合は PR 作成後に `gh pr merge --squash` を実行する

`push_gate.py` が見つからない、または import に失敗した場合は警告を出して gate 検証を skip します。
これは関連 task の実装順差異を吸収するための互換動作です。

## 6 ゲート

`helix pr --gate` が利用する 6 ゲートは `helix push --gate` と同一です。

| ID | 名前 | 検証内容 | fail 時メッセージ |
| --- | --- | --- | --- |
| `G-tests` | pytest / bats | `python3 -m pytest cli/lib/tests/ -q` と `bats cli/tests` | テスト fail を修正してから再実行 |
| `G-catalog` | command catalog | `python3 -m pytest cli/lib/tests/test_command_catalog.py -q` | help/docs 同期不足、`helix commands` 確認 |
| `G-secret` | secret scan | `pre-commit run --all-files` | secret detected、staged change を確認 |
| `G-ff` | fast-forward | `git fetch <remote> <branch>` 後に `git merge-base --is-ancestor <remote>/<branch> HEAD` | rebase 必要、`git pull --rebase origin main` |
| `G-attr` | Co-Authored-By | `git rev-list --count <remote>/<branch>..HEAD` と `git log <remote>/<branch>..HEAD --grep "Co-Authored-By"` を比較 | commit 修正必要 (amend or rebase -i) |
| `G-nondestructive` | destructive diff | `git diff <remote>/<branch>..HEAD` の追加行から危険パターンを検出 | destructive operation 検出、manual-confirm 必要 |

`--base` を指定した場合、gate helper が `branch` 引数を受け取れる実装であれば同じ branch 名を gate 側にも渡します。

## 自動生成される PR 本文

`--body` を指定しない場合、本文は以下から組み立てます。

- `git log <base>..HEAD --oneline` の先頭 20 件
- Conventional Commits の `feat` / `fix` / `docs` から作る release notes
- `phase.yaml` に残っている gate table
- sprint status
- `git diff --stat <base>..HEAD`
- 最低限の test plan checklist

このため `helix pr --dry-run` は、PR を作る前の本文確認にも使えます。

## 出力例

### `helix pr --dry-run`

```text
=== PR Preview ===
Title: feature/pr-gate
Base:  main
Branch: feature/pr-gate

## Summary
abcd123 feat: add pr gate

## Release Notes
### 新機能
- abcd123 feat: add pr gate
```

### `helix pr --gate --dry-run`

```text
Gate validation: passed
Gate validation completed (dry-run); PR creation skipped.
```

### `helix pr --gate`

```text
Gate validation: passed
https://github.com/example/repo/pull/123
```

### `helix pr --gate --auto-merge`

```text
Gate validation: passed
https://github.com/example/repo/pull/123
Merged pull request #123
```

## exit code

| code | 意味 |
| --- | --- |
| `0` | PR 作成成功、または `--gate --dry-run` / preview 成功、または auto-merge 成功 |
| `1` | gate fail、PR 作成失敗、auto-merge 失敗 |
| `2` | 入力エラー |

## 注意点

- `--auto-merge` は `--gate` 必須です
- `gh` が無い環境では PR 作成も auto-merge もできません
- `--gate` なしの既存モードでは `phase.yaml` を参照し、`--force` でのみ gate 未通過をバイパスできます
- `--gate` ありの dry-run は preview ではなく検証専用です
- `--body` を指定した場合は自動生成本文を置き換えます

## 関連

- `cli/helix-pr`
- `cli/lib/push_gate.py`
- [push.md](push.md)
- [index.md](index.md)
