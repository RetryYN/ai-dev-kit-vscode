---
doc_id: process-L11
title: "L11 総合レビュー + ユーザー検証 + 要件巻き取り"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L11
pairs_with: null
canonical_source: HELIX-workflows/helix-process/L11-final-review.md
---

# L11 総合レビュー + ユーザー検証 + 要件巻き取り

## 入力

- L9 総合テスト完遂物
- L10 UX 磨き上げ完遂物 (UI 案件)
- L1 業務要求 / L3 要件
- skill: `workflow/verification` / `workflow/quality-lv5` / `workflow/adversarial-review`

## 進め方

### Step 1: 総合レビュー (内部、PM + TL)
- L1 業務要求 + L3 要件 ↔ 実装 + テスト結果の全体一致確認
- 全工程の成果物 (L1〜L10) を sweep し、V-model 4 artifact 双方向 trace 完備を確認

### Step 2: ユーザー検証 (Beta / UAT)
- 実ユーザー or PO によるシナリオ検証
- フィードバック収集

### Step 3: 要件巻き取り (フィードバック → L1/L3)
- ユーザー検証で「要件追加・修正必要」が出たら **L1 業務要求 or L3 要件に追記**
- 次イテレーションの input になる

### Step 4: G11 総合レビュー通過判定

## 成果物

- **総合レビュー記録**: `docs/v2/L11-review/<area>-review-result.md`
- **ユーザー検証フィードバック**: `docs/v2/L11-review/<area>-user-feedback.md`
- **要件巻き取り pull-back**: L1 / L3 doc 追記

## ペア凍結相手

なし (V-model 中段の総合レビュー)

## ゲート

- **G11 総合レビュー通過ゲート**: PM + PO 判定

## 関連 skill

- `workflow/verification`
- `workflow/quality-lv5`
- `workflow/adversarial-review`
- `common/code-review`

## アンチパターン

- ❌ ユーザー検証を skip (L12 デプロイ後の事故リスク)
- ❌ フィードバックを次工程に持ち越さない (要件巻き取りなしで L12 デプロイ)
- ❌ PLAN 起票

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L11-final-review.md](../../../HELIX-workflows/helix-process/L11-final-review.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（検証フェーズ） |
| 入力 | L10・L1 要求定義・L3 要件定義 |
| 出力 | L12 への入力 |
| 対応する設計 | L1 要求定義・L3 要件定義（最終突合） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L11-総合レビューplan`
- 全工程成果物の整合レビュー

### `L11-ユーザー検証plan`
- ユーザー視点での検証

### `L11-要件巻き取りplan`
- 未充足要件・変更要件の巻き取り

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

