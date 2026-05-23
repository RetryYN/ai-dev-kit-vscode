---
doc_id: process-L05
title: "L5 詳細設計 + 結合テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L5
pairs_with: L8
---

# L5 詳細設計 + 結合テスト設計

## 入力

- L4 基本設計 + ADR (必須)
- skill: `workflow/api-contract` / `workflow/design-doc` / `project/db` / `project/api`

## 進め方

### Step 1: モジュール分割 + 契約境界
- L4 アーキテクチャを **モジュール / コンポーネント** に分割
- 各モジュール間の **契約境界** を確定 (D-API / D-DB / D-CONTRACT / D-STATE)

### Step 2: D-API / D-DB / D-CONTRACT 詳細設計
- endpoint 仕様 / class signature / table schema / 契約 (BE-FE / external / agent 間)
- 各 1 file 1 設計単位

### Step 3: 結合テスト設計のペア凍結 (V-model L8 ペア)
- モジュール結合点ごとに **結合テスト** を設計
- `docs/v2/L8-test-design/<feature>-integration-test-design.md` に pair として書く

### Step 4: G5 詳細設計凍結ゲート通過 (API/Schema Freeze)

## 成果物

- **正本**: `docs/v2/L5-detailed-design/{D-API,D-DB,D-CONTRACT,D-STATE}/<feature>.md`
- **ペア artifact**: `docs/v2/L8-test-design/<feature>-integration-test-design.md`

## ペア凍結相手

L8 結合テスト

## ゲート

- **G5 詳細設計凍結ゲート**: TL + PM 判定、API/Schema Freeze + V-model 結合テスト設計ペア凍結

## 関連 skill

- `workflow/api-contract` (D-API 契約本体)
- `workflow/design-doc`
- `project/db` / `project/api` / `project/ui`

## アンチパターン

- ❌ 契約境界なし (BE-FE 間で後追い実装擦り合わせ、Phase B コンフリクト)
- ❌ 結合テスト設計のペア凍結を skip (V-model 違反、L8 結合テストが空回り)
- ❌ 詳細設計を PLAN.md 内に書く (PLAN は L7 のみ)
