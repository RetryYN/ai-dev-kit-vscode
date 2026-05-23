---
doc_id: process-L02
title: "L2 画面設計・フロント UI / ワイヤーモック作成"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L2
pairs_with: L10
canonical_source: HELIX-workflows/helix-process/L2-ui-design.md
---

# L2 画面設計・フロント UI / ワイヤーモック作成

## 入力

- L1 業務要求 (必須)
- skill: `common/visual-design` / `design-tools/web-system` / `agent-skills/mock-driven-development` / `project/ui`
- **工程専門 workflow (FE 弱点補強)**: [screen-design-workflow.md](../../../HELIX-workflows/helix-process/screen-design-workflow.md) — IA → 画面一覧/遷移 → ワイヤー (Low-Fi → High-Fi) → モック → プロトタイプ → UT → コンポーネント化。補強する FE detector = `state-transition-drift` / `mock-promotion`

## 進め方

### Step 1: 情報設計 (IA) + 画面リスト
- 業務要求から **画面リスト** + **画面遷移** を起こす
- `agent-skills/mock-driven-development` の三点セット (information / layout / ux) を確立

### Step 2: ワイヤーモック作成
- HTML/Tailwind/shadcn or Figma 等で **触れる mock** を作る
- mock 自体が成果物 (静的画像ではなく、状態遷移 + イベント定義含む)

### Step 3: state-events 定義 (フロント駆動契約)
- mock から `state-events.md` を起こす (BE/FE 接続点)
- L3 要件 / L5 詳細設計の API 契約導出元になる

### Step 4: UX 磨き上げのペア凍結 (V-model L10 ペア)
- mock のうち「磨き上げ余地」を L10 carry note として明示
- 本工程は構造、L10 で美的最適化

### Step 5: G2 mock 凍結ゲート通過 (UX 承認)
- mock + state-events 凍結 → MOCK-* auto-enqueue 発火 (HELIX 既存 framework)

## 成果物

- **正本**: `docs/v2/L2-screen-design/<area>/mock.html` (or Figma export)
- **state-events**: `docs/v2/L2-screen-design/<area>/state-events.md`
- **画面遷移図**: `docs/v2/L2-screen-design/<area>/screen-flow.md`
- **ペア carry**: `docs/v2/L10-ux-polish/<area>/polish-carry.md`

## ペア凍結相手

L10 フロント UX・ビジネスデザイン磨き上げ

## ゲート

- **G2 mock 凍結ゲート**: TL + PM + UX 判定、UI なし案件は skip

## 関連 skill

- `common/visual-design`
- `design-tools/web-system` (shadcn / デザイントークン)
- `design-tools/diagram` / `design-tools/gpt-image`
- `agent-skills/mock-driven-development`
- `agent-skills/frontend-ui-engineering`
- `project/ui`

## アンチパターン

- ❌ UI なし案件で本工程を実施 (be 駆動なら skip)
- ❌ mock なしで L3 要件定義に進む (画面 → 要件導出が機能しない)
- ❌ state-events なしで mock 単独凍結 (BE 契約が後追いで割れる)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L2-ui-design.md](../../../HELIX-workflows/helix-process/L2-ui-design.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ） |
| 入力 | L1 要求定義 |
| 出力 | L3 要件定義 への入力 |
| ペアとなるテスト設計 | ワイヤーモック作成（右腕 L10 フロントUX・ビジネスデザイン磨き上げで実行） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L2-画面一覧plan`
- 画面一覧
- 画面 ID
- 各画面の役割・目的

### `L2-画面遷移plan`
- 画面遷移図
- 遷移条件
- イベントと遷移先

### `L2-ワイヤーフレームplan`
- 各画面のワイヤーフレーム
- レイアウト構成
- 情報配置

### `L2-UI要素plan`
- 主要 UI コンポーネント
- 入力要素・表示要素
- 操作要素

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

