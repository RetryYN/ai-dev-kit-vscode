---
name: six-stage-review
description: 現在の差分を6段階（Format/Lint/Style/Logic/Design/Architecture）でレビューする
---

# 6段階コードレビュー

現在の変更を6段階に分けてレビューし、Approve判断サマリを出力する。

## スコープ

レビュー対象を以下の優先順で決める:
1. 引数で指定された範囲（PR番号・ファイル・コミット範囲）
2. `git diff --staged`
3. `git diff main...HEAD`

仕様書・ADR・命名規則ファイル（`.coderabbit.yaml`, `CONTRIBUTING.md`, `CLAUDE.md`, `docs/` 等）を探して読む。なければ「仕様書なし＝仕様由来エッジケース未検証」と明記する。

## 実行

以下のサブエージェントを並列起動する（Stage 1–2 はツールゲートに委ねるため割愛）:

- `logic-reviewer`（Stage 4 Logic / 仕様照合・逆説ルール）
- `security-reviewer`（Stage 4 セキュリティ / すべてブロッキング扱い）
- `design-reviewer`（Stage 5 Design / 機械的ヒントまで）

Stage 3（Style）は軽量なので本コマンド内で直接点検する。
Stage 6（Architecture）は差分がシステム境界・認証範囲・データフロー・デプロイ単位に触れる場合のみ「ADRで事前決定すべき」と警告する。

## 統合と出力

各サブエージェントの結果を統合し、以下の形式で出力する:

```
## レビュー結果: <対象>

### サマリ
- ブロッキング: N件 / 要確認: M件
- 仕様書: あり / なし

### Stage 3 Style
### Stage 4 Logic（★最重要）
  - ブロッキング / 要確認
  - ⚠️ AI指摘ゼロだった重点確認領域
### Stage 5 Design（ヒント / 人間判断）
### Stage 6 Architecture（ADR要否の警告のみ）

### Approve判断
[ ] Stage 1-2 / [ ] Stage 3 / [ ] Stage 4 仕様照合 / [ ] Stage 5 / [ ] Stage 6 ADR整合
→ 推奨: Approve可 / 条件付き / 保留
```

## 原則

- AIのレビューを Approve の根拠にしない。仕様判断の最終責任は人間。
- 逆説ルール: AIが指摘しなかった箇所こそ人間が念入りに見る。AIコメントゼロを「安全」と判断しない。
- AI比率は目安であって定量ゲートではない。
