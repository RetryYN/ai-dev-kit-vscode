---
doc_id: process-L14
title: "L14 運用検証 + 機能改善"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L14
pairs_with: L1
---

# L14 運用検証 + 機能改善

## 入力

- L13 デプロイ後検証完遂物
- L1 業務要求 + L14 運用テスト設計 (L1 でペア凍結済)
- 運用 KPI (SLO / SLI / 業務指標)
- skill: `workflow/observability-sre` / `workflow/postmortem` / `advanced/innovation-mgr`

## 進め方

### Step 1: 運用テスト実施 (V-model L1 ペア)
- L1 でペア凍結された **運用テスト** を実環境で実施
- 業務要求が想定通り運用フェーズで機能するか検証

### Step 2: 運用 KPI 観測 + 業務影響分析
- SLO / SLI / 業務指標を継続観測
- 想定 KPI と実測の gap を分析

### Step 3: 機能改善 (次イテレーション input)
- 運用フィードバック → L1 業務要求の追加 / 修正
- 次イテレーションの L0 企画書 input になる

### Step 4: 運用学習 / 知見蓄積
- postmortem 蓄積、運用 doc 更新

### Step 5: G14 運用学習完了ゲート

## 成果物

- **運用テスト結果**: `docs/v2/L14-test-results/<area>-operational-test-result.md`
- **運用 KPI 記録**: `docs/v2/L14-operations/<area>-kpi-log.md`
- **機能改善 pull-back**: L1 業務要求 追記 / 次イテレーション L0 企画書 input
- **postmortem アーカイブ**: `docs/v2/L14-postmortems/`

## ペア凍結相手 (上流対応)

L1 要求定義 (L1 でペア凍結された運用テストを本工程で実施)

## ゲート

- **G14 運用学習完了ゲート**: PM 判定、運用 KPI 維持 + 改善 backlog 整理

## 関連 skill

- `workflow/observability-sre`
- `workflow/postmortem`
- `workflow/incident`
- `advanced/innovation-mgr` (次イテレーション企画接続)
- `agent-skills/deprecation-and-migration` (機能廃止)

## アンチパターン

- ❌ L1 でペア凍結されていない運用テストを本工程で起こす (V-model 違反、L1 差し戻し)
- ❌ KPI 観測なし運用 (業務影響不明)
- ❌ フィードバック → L1 巻き取りを skip (次イテレーションに知見が継承されない)
- ❌ PLAN 起票
