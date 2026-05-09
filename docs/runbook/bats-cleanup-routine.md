# bats-cleanup Routine

`helix test` は完了時に `helix bats-cleanup --list` を実行し、`/tmp` に `bats-run-*` / `bats-test-*` が 5 件以上残っていれば warning を表示する。

## 目的

- Bats 実行後に一時ディレクトリの残存を早めに検知する
- 自動削除は避け、誤削除リスクを人間確認に寄せる

## 通常運用

1. `helix test` 実行後、warning の有無を確認する
2. warning が出たら `helix bats-cleanup --list` で残存一覧と `marker=YES/NO` を確認する
3. 5 件以上残っていたら、まず削除対象を人間が確認する
4. HELIX marker があり削除してよいものだけ `helix bats-cleanup --delete --older-than <N>` で削除する

## 推奨コマンド

```bash
helix bats-cleanup --list
helix bats-cleanup --help
helix bats-cleanup --delete --older-than 0
```

## Warning の意味

- warning は `helix test` の post-run hook が表示する運用通知で、テスト結果の pass/fail 自体は変えない
- 自動 `--delete` は実行しない。誤削除リスクがあるため、一覧確認後に明示実行する
- `--delete` は `--older-than <N>` 必須で、直後に消す場合も `0` を明示する

## 注意

- 本 PLAN では自動 `--delete` は実装しない
- marker がないディレクトリは `helix bats-cleanup` 側で削除対象外のまま維持する
- warning は運用導線であり、`helix test` 自体の pass/fail 判定は変えない
