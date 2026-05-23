---
doc_id: process-L10
title: "L10 フロント UX・ビジネスデザイン磨き上げ"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L10
pairs_with: L2
canonical_source: HELIX-workflows/helix-process/L10-ux-refinement.md
---

# L10 フロント UX・ビジネスデザイン磨き上げ

## 入力

- L2 画面設計 + mock + state-events (必須、UI 案件)
- L9 総合テスト完遂物 (機能は動く前提)
- L2 carry note (磨き上げ余地)
- skill: `common/visual-design` / `design-tools/web-system` / `writing/god-writing` / `agent-skills/frontend-ui-engineering`
- **工程専門 workflow (FE 弱点補強)**: [frontend-design-workflow.md](../../../HELIX-workflows/helix-process/frontend-design-workflow.md) — ビジュアル → デザインシステム/トークン → a11y → ビジュアル回帰 → UX 磨き → ビジネスデザイン磨き。補強する FE detector = `design-token-drift` / `a11y-regression` / `visual-regression`

## 進め方

### Step 1: UX 監査 + 改善点抽出
- L2 mock と実装後 UI を比較、UX gap を抽出
- DESIGNER.md 9 セクション (情報 / レイアウト / UX / モーション / a11y / データ viz / 等) で評価

### Step 2: コピー磨き + ビジネスデザイン
- LP / オンボーディング / エラーメッセージのコピー磨き上げ (skill: `writing/god-writing`)
- 心理 trigger (emotional / social proof / urgency / trust) を意識

### Step 3: a11y / 国際化チェック
- WCAG / axe-core で a11y 検証
- 国際化 (i18n) があれば対応

### Step 4: G10 UX 磨き通過判定 (UI 案件のみ)

## 成果物

- **磨き上げ後 UI** (本体実装に reflect)
- **UX 監査記録**: `docs/v2/L10-ux-polish/<area>-ux-audit.md`

## ペア凍結相手 (上流対応)

L2 画面設計

## ゲート

- **G10 UX 磨き通過ゲート**: UI 案件のみ、UX + PM 判定

## 関連 skill

- `common/visual-design`
- `design-tools/web-system`
- `design-tools/gpt-image` (アイキャッチ / LP ヒーロー)
- `writing/god-writing` (コピー)
- `automation/browser-script` (axe-core)
- `agent-skills/frontend-ui-engineering`

## アンチパターン

- ❌ L2 mock を再構築 (L2 工程に戻る、L10 は磨きのみ)
- ❌ PLAN 起票 (磨き上げは本体実装内、PLAN は L7 のみ)
- ❌ UI なし案件で本工程実施 (skip)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L10-ux-refinement.md](../../../HELIX-workflows/helix-process/L10-ux-refinement.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 右腕（検証フェーズ） |
| 入力 | L9 総合テスト・L2 画面設計 |
| 出力 | L11 への入力 |
| 対応する設計 | L2 画面設計・フロントUI / ワイヤーモック |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L10-UX磨き上げplan`
- UI / UX 改善
- 操作性向上

### `L10-ビジネスデザインplan`
- ビジネス価値の磨き上げ

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

