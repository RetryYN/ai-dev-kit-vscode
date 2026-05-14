# helix push

## 概要

`helix push` は、push 前に 6 つの機械ゲートをまとめて検証し、
条件を満たしたときだけ `git push` を実行するための補助 CLI です。

対象は `origin/main` を既定にした通常の push 導線で、
`--execute` を付けない限りは dry-run として動作します。

主な用途:

- push 前に test / catalog / secret / fast-forward 条件を一括確認する
- Co-Authored-By と destructive diff の見落としを減らす
- 手元で安全に「今の branch は push 可能か」を機械判定する

`cli/helix` dispatcher への登録は別 task で行う前提のため、
この task では `cli/helix-push` を直接呼び出します。

## 書式

```text
helix push --gate [--execute] [--remote REMOTE] [--branch BRANCH]
```

実行例:

```bash
helix push --gate
helix push --gate --execute
helix push --gate --execute --remote origin --branch main
```

## オプション

| オプション | 説明 |
| --- | --- |
| `--gate` | 6 ゲート検証を有効化。現状は必須 |
| `--execute` | 全ゲート PASS 時のみ `git push <remote> <branch>` を実行 |
| `--remote REMOTE` | 検証対象と push 対象の remote。既定は `origin` |
| `--branch BRANCH` | 検証対象と push 対象の branch。既定は `main` |
| `--help` | ヘルプを表示 |

## 6 ゲート

| ID | 名前 | 検証内容 | fail 時メッセージ |
| --- | --- | --- | --- |
| `G-tests` | pytest / bats | `python3 -m pytest cli/lib/tests/ -q` と `bats cli/tests/*.bats` 相当 | テスト fail を修正してから再実行 |
| `G-catalog` | command catalog | `python3 -m pytest cli/lib/tests/test_command_catalog.py -q` | help/docs 同期不足、`helix commands` 確認 |
| `G-secret` | secret scan | `pre-commit run --all-files` | secret detected、staged change を確認 |
| `G-ff` | fast-forward | `git fetch <remote> <branch>` 後に `git merge-base --is-ancestor <remote>/<branch> HEAD` | rebase 必要、`git pull --rebase origin main` |
| `G-attr` | Co-Authored-By | `git rev-list --count <remote>/<branch>..HEAD` と `git log <remote>/<branch>..HEAD --grep "Co-Authored-By"` を比較 | commit 修正必要 (amend or rebase -i) |
| `G-nondestructive` | destructive diff | `git diff <remote>/<branch>..HEAD` の追加行から `DROP TABLE` / `git branch -D` / `rm -rf` / `--force` / `--no-verify` を検出 | destructive operation 検出、manual-confirm 必要 |

## 出力形式

dry-run 成功時:

```text
[helix push] gate verification...
✓ G-tests          (pytest 1147 + bats 452)
✓ G-catalog        (4 PASS)
✓ G-secret         (pre-commit PASS)
✓ G-ff             (origin/main fast-forward OK)
✓ G-attr           (10 commits / 10 with Co-Authored-By)
✓ G-nondestructive (no destructive pattern)

[helix push] all gates PASS
```

`--execute` 成功時:

```text
[helix push] gate verification...
✓ G-tests          (pytest 1147 + bats 452)
✓ G-catalog        (4 PASS)
✓ G-secret         (pre-commit PASS)
✓ G-ff             (origin/main fast-forward OK)
✓ G-attr           (10 commits / 10 with Co-Authored-By)
✓ G-nondestructive (no destructive pattern)

[helix push] all gates PASS -> executing git push origin main
```

失敗時:

```text
[helix push] gate verification...
✓ G-tests          (pytest 1147 + bats 452)
✗ G-catalog        (test_command_catalog FAIL: missing routed command 'X')
  Fix: help/docs 同期不足、`helix commands` 確認

[helix push] BLOCKED (1 gate failed)
```

## exit code

| code | 意味 |
| --- | --- |
| `0` | 全 PASS (`--execute` なし) または push 成功 (`--execute` あり) |
| `1` | 1 つ以上の gate が fail、または push 自体が失敗 |
| `2` | 入力エラー |

## 実装構成

- `cli/helix-push`
  - bash の entrypoint
  - `--gate` 必須チェック
  - `--execute` / `--remote` / `--branch` の引数解釈
  - Python helper への委譲
- `cli/lib/push_gate.py`
  - 6 ゲートの実処理
  - ゲート結果の集計
  - `--execute` 時の `git push`
  - CLI 向けの整形出力

shell 側は薄く保ち、判定ロジックの正本は helper に寄せています。
これにより pytest で各ゲート関数を個別に固定しやすくしています。

## 安全性

- `--execute` を付けない限り `git push` は実行しません
- `git fetch` / `git diff` / `git log` / `pre-commit` は検証目的でのみ使用します
- destructive diff は追加行ベースで検出し、危険な変更候補を fail-close で止めます
- `Co-Authored-By` は ahead commits 数と grep hit 数を比較して抜け漏れを検知します

## テスト

対象テスト:

- `python3 -m pytest cli/lib/tests/test_helix_push.py -q`
- `bats cli/tests/helix-push.bats`

想定確認内容:

- helper 単体で各ゲートが期待どおり pass/fail する
- CLI が `--gate` 必須、`--help`、不正オプションを正しく扱う
- `--execute` 時に全ゲート PASS なら remote へ push される
- いずれかの gate が fail した場合は push されない

## 関連

- `helix pr`
  - PR 本文生成の導線
- `docs/commands/index.md`
  - 公開コマンド一覧。dispatcher 登録 task 完了後に同期対象になる
- `cli/lib/tests/test_command_catalog.py`
  - help / docs / routing 契約の機械検証
