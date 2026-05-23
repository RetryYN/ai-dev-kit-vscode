---
doc_id: process-L03
title: "L3 要件定義 + 受入テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L3
pairs_with: L12
---

# L3 要件定義 + 受入テスト設計

## 入力

- L1 業務要求 (必須)
- L2 画面設計 + state-events (UI 案件、必須)
- skill: `workflow/requirements-deriver` / `workflow/api-contract` (方針) / `agent-skills/spec-driven-development`

## 進め方

### Step 1: システム機能要件 (FR) の確定
- L1 業務要求 + L2 mock から **システム機能要件** (FR-*) を導出
- L1 BR と L3 FR の双方向 trace 確立

### Step 2: 受入条件 (AC) の確定
- 各 FR に対応する **受入条件** (AC-*) を確定 (PO が「これが満たされれば受入」と判定可能な粒度)

### Step 3: 受入テスト設計のペア凍結 (V-model L12 ペア)
- AC ごとに **受入テスト** を設計
- `docs/v2/L12-test-design/<area>-acceptance-test-design.md` に pair として書く

### Step 4: G3 要件凍結ゲート通過 (PM + PO 判定)
- FR + AC + 受入テスト設計 ペア凍結を PO 判定

## 成果物

- **正本**: `docs/v2/L3-requirements/<area>-functional-requirements.md` (FR-* + AC-*)
- **ペア artifact**: `docs/v2/L12-test-design/<area>-acceptance-test-design.md` (受入テスト設計)

## ペア凍結相手

L12 デプロイ + 受入テスト

## ゲート

- **G3 要件凍結ゲート**: PM + PO 判定

## 関連 skill

- `workflow/requirements-deriver`
- `workflow/api-contract` (方針、本格契約は L5)
- `agent-skills/spec-driven-development`

## アンチパターン

- ❌ AC なしで G3 を通す (受入工程で判定不能)
- ❌ L1 業務要求を skip して直接 FR に飛ぶ (ビジネス trace 不在)
- ❌ 受入テスト設計を後回し (V-model 違反、L12 で受入工程が空回り)
