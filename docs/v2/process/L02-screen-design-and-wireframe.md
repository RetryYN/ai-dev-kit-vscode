---
doc_id: process-L02
title: "L2 画面設計・フロント UI / ワイヤーモック作成"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L2
pairs_with: L10
---

# L2 画面設計・フロント UI / ワイヤーモック作成

## 入力

- L1 業務要求 (必須)
- skill: `common/visual-design` / `design-tools/web-system` / `agent-skills/mock-driven-development` / `project/ui`

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
