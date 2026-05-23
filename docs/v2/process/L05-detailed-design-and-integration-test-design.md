---
doc_id: process-L05
title: "L5 詳細設計 + 結合テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L5
pairs_with: L8
canonical_source: HELIX-workflows/helix-process/L5-detailed-design.md
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

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L5-detailed-design.md](../../../HELIX-workflows/helix-process/L5-detailed-design.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ） |
| 入力 | L4 基本設計 |
| 出力 | L6 機能設計 への入力 |
| ペアとなるテスト設計 | 結合テスト設計（右腕 L8 結合テストで実行） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L5-内部処理設計plan`
- モジュール内部処理
- 処理フロー

### `L5-モジュール分割plan`
- モジュール構成
- 責務分担

### `L5-物理データ設計plan`
- 物理テーブル
- インデックス戦略

### `L5-IF詳細設計plan`
- 入出力詳細
- エラー処理

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

