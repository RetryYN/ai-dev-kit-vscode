---
doc_id: process-L3-detailed-design
title: "L3 詳細設計工程の進め方"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L3
pairs_with_test_phase: L4_integration_unit
---

# L3 詳細設計工程の進め方

## 入力

- `docs/v2/L2-MASTER.md` / `docs/v2/CONCEPT.md` / `docs/adr/ADR-*.md` (L2 工程の成果物、必須)
- 既存 L3 詳細設計 (`docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT}/*.md`)
- skill: `workflow/api-contract` (D-API) / `workflow/design-doc` / `workflow/schedule-wbs` / `project/db` / `project/api`

## 進め方

### Step 1: L2 設計を L3 単位に分解
- L2 大局判断を **D-API / D-DB / D-CONTRACT / D-STATE / D-UI** 等の機能設計単位に分解
- 各単位は `docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT}/<feature>.md` として 1 file 1 設計

### Step 2: 詳細設計の機能仕様確定
- D-API: endpoint 仕様 / class signature / 関数 schema (input/output/error)
- D-DB: table schema / index / FK / migration 手順
- D-CONTRACT: 契約境界 (BE-FE / external API / agent 間)
- D-STATE: 状態遷移 (UI 案件 / agent 案件)

### Step 3: 機能設計 ↔ 単体テスト設計のペア凍結
- 機能設計 (1 関数 / 1 endpoint) ごとに **単体テスト設計** を pair で確定
- `docs/v2/L4-test-design/<feature>-unit-test-design.md` (V-model 4 artifact ③)
- 業界 standard: IEEE 829-2008 / ISO/IEC/IEEE 29119-3:2021 (case 構造: precondition / input / expected / postcondition)

### Step 4: 詳細設計 ↔ 結合テスト設計のペア凍結
- 機能間結合の **結合テスト設計** を pair で確定
- `docs/v2/L4-test-design/<feature>-integration-test-design.md`

### Step 5: 工程表 (WBS) 作成
- L3 設計から L4 実装に渡す **WBS** を作成
- skill: `workflow/schedule-wbs`
- 各 WBS item は 1 つの L4 PLAN に対応

### Step 6: G3 ゲート通過判定
- API/Schema Freeze + 事前調査 + V-model 結合/単体テスト設計ペア凍結

## 成果物

- **正本**: `docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT,D-STATE,D-UI}/<feature>.md`
- **ペア artifact**:
  - `docs/v2/L4-test-design/<feature>-unit-test-design.md` (単体テスト設計、機能設計と pair)
  - `docs/v2/L4-test-design/<feature>-integration-test-design.md` (結合テスト設計、詳細設計と pair)
- **工程表**: `docs/v2/L3-detailed-design/schedule/<area>-wbs.md` or `.helix/task-plan.yaml`

## PLAN は出力しない (但し L4 PLAN を起こすための parent_design path がここで確定)

L3 詳細設計工程の成果物は **doc + 工程表のみ**。L4 PLAN は **本工程の成果物 (L3 設計 doc) を parent_design として参照する subordinate** として L4 工程で起票される。

L4 PLAN の frontmatter には必ず `parent_design: docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT}/<feature>.md` (または該当 L2 doc) を記載すること。

## ゲート

- **G3 (実装着手ゲート)**: TL + PM 判定、API/Schema Freeze + V-model 結合/単体テスト設計ペア凍結
- **G3.functional_freeze (サブゲート)**: size=L / drive in (fe/fullstack/db) で必須 (CONCEPT.md §5 line 314)

## 関連 skill

- `workflow/api-contract` (D-API 契約)
- `workflow/design-doc` (設計 doc 作成)
- `workflow/schedule-wbs` (工程表)
- `workflow/threat-model` (セキュリティ①継続)
- `project/db` / `project/api` / `project/ui`

## アンチパターン

- ❌ L3 詳細設計 doc を PLAN.md 内に埋め込む (PLAN 単位で詳細が散在、設計の再利用不能)
- ❌ 単体テスト設計 / 結合テスト設計のペア凍結を skip (V-model 違反、G3 通過不能)
- ❌ L4 PLAN を `parent_design:` 不在で起票 (本工程の成果物への subordinate でなくなる、本 V-model 違反は本日 2026-05-24 PLAN-156/224 で発覚)
- ❌ 工程表なしで L4 実装に進む (Sprint 順序 / 並列衝突判定が不能)
