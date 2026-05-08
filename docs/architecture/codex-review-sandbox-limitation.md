# helix review --uncommitted の sandbox 制約（read-only 回避ルール）

## 1. 目的

`helix review --uncommitted` を `sandbox=read-only` で実行した際に発生する
`Failed to initialize session: Read-only file system` エラーを、運用上どのように回避するかを明文化する。

本ドキュメントは PLAN-034 の W-3 で作成する短期回避策の記録であり、production fix は PLAN-035 へ carry する。

## 2. 現象

- 代表症状:
  - `Failed to initialize session: Read-only file system`
  - `fatal: could not initialize session` 系の継続失敗
- 発生文脈:
  - `helix review --uncommitted` 実行時
  - 実行プロセスが一時的に書き込みを要求する箇所があるにもかかわらず、sandbox が read-only の場合

## 3. 既知の挙動確認

PLAN-033 で W-1 / W-2 / W-3 の **3 連続委譲先で** 同一エラーを再現した:

```
$ helix review --uncommitted
[helix-review] レビュー開始...
Failed to initialize session: Read-only file system
[helix-review] FAIL: レビューを手動で再実行してください: helix review --uncommitted
[helix-review] 完了 (exit=1) → /tmp/helix-review/review-20260509-051020.log
```

すべて `helix codex --sandbox read-only` で起動した子セッション内で `codex review --uncommitted` を呼んだ場合に発生 (cli/helix-codex:1071 で `HELIX_CODEX_INTERNAL=1` 設定済の文脈)。Codex CLI 側の session init が write を要求し、helix-codex の sandbox=read-only と衝突している。

実環境では `helix code find "..."` も同様に SQLite の write 要求で失敗するケースを観測 (read-only sandbox が SQLite open mode と衝突)。

## 4. 根本原因（暫定）

- 原則:
  - `helix review` は review 実行のための一時ディレクトリや session 情報を作成しようとする
  - sandbox=read-only ではこの初期化が阻害される
- 関連 carry:
  - PLAN-033 retro の該当項目が継続して再現される
- 影響:
  - read-only 委譲経路ではレビュー工程がブロックされ、判断結果が遅延する

## 5. 本ドキュメントの短期回避ルール

### 5.1 原則

- read-only 環境で `helix review --uncommitted` を実行しない
- `helix codex` にて read-only 委譲が完了した後のレビューは、必要に応じて workspace-write へ切替
- 代替ルートは Opus 経由での review 実行を優先

### 5.2 実施チェックリスト

1. 現在の sandbox が read-only か確認
2. read-only の場合は下記で代替:
   - そのまま `helix review --uncommitted` を再試行しない
   - 実害ログを残し、別セッション（workspace-write）へ切替
   - 報告は「review skip ではなく、sandbox 制約による遅延」と明示
3. 修正完了後、受入時に `helix review --uncommitted` が実行できる環境で最終レビューステータスを取得

## 6. 運用運搬ルール

### 6.1 委譲設計での扱い

- W-12 のような code 実装 carry が read-only 制約下にある場合、レビューを同一セッションで完了しない
- 役割上の実行者を明示:
  - 実装: Codex
  - 最終 review: Opus / workspace-write 相当経路

### 6.2 将来代替（最終的には実装）

- `helix review --uncommitted` の session init の書き込み先を read-only でも成立する設計に切替える
- ただしこの production fix は本 PLAN では未実施
- 対象: PLAN-035

## 7. PLAN-035 引継ぎ

- 引継ぎ先: `PLAN-035`
- carry 内容:
  - read-only 環境での `helix review --uncommitted` session init fail を production 仕様として解消する
  - 必要なら review 実行の中間生成物保存先を調整
- 成果物条件:
  - read-only でも review の初期化が成立すること
  - 既存 REVIEW フロー回帰なし

## 8. 参考

- [docs/plans/PLAN-034-codex-output-and-prompt-template.md](../plans/PLAN-034-codex-output-and-prompt-template.md)
- [docs/plans/PLAN-033-drift-check-and-baseline-cleanup.md](../plans/PLAN-033-drift-check-and-baseline-cleanup.md)

## 9. 残存アクション

- [ ] PLAN-035 起票の実施
- [ ] review session init の読み取り専用互換実装
- [ ] 回避ルールを運用ドキュメント（retries / handover）へ反映
