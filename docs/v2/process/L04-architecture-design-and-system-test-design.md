---
doc_id: process-L04
title: "L4 基本設計 + 総合テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L4
pairs_with: L9
canonical_source: HELIX-workflows/helix-process/L4-basic-design.md
---

# L4 基本設計 + 総合テスト設計

## 入力

- L3 システム機能要件 + AC (必須)
- skill: `workflow/design-doc` / `workflow/adversarial-review` / `workflow/api-contract` / `common/visual-design`

## 進め方

### Step 1: アーキテクチャ + 大局判断
- システム全体構造 (BE / FE / DB / 外部連携 / agent 構成) を確定
- 大局判断ごとに **ADR snapshot** を起票 (`docs/adr/ADR-NNN-<topic>.md`)

### Step 2: 業界 standard 整合
- PLAN-087 ガード: Web 検索 3 query 必須
- IEEE 42010 / arc42 / C4 / Diátaxis 等の整合

### Step 3: tl-advisor adversarial check (mandatory)
- 大局判断ごとに `helix codex --role tl-advisor` 召喚
- changes_required 判定なら全 P0/P1 反映後に再召喚

### Step 4: 総合テスト設計のペア凍結 (V-model L9 ペア)
- アーキテクチャごとに **総合テスト** (system test) を設計
- `docs/v2/L9-test-design/<area>-system-test-design.md` に pair として書く
- 業界 standard: IEEE 829-2008 / ISO 29119-3 case 構造

### Step 5: G4 基本設計凍結ゲート通過

## 成果物

- **正本**: `docs/v2/L4-architecture/<area>-architecture.md`
- **ADR snapshot**: `docs/adr/ADR-NNN-<topic>.md`
- **ペア artifact**: `docs/v2/L9-test-design/<area>-system-test-design.md`

## ペア凍結相手

L9 総合テスト

## ゲート

- **G4 基本設計凍結ゲート**: TL + PM 判定、adversarial-review + セキュリティ① + V-model 総合テスト設計ペア凍結

## 関連 skill

- `workflow/design-doc`
- `workflow/adversarial-review` (tl-advisor 召喚、mandatory)
- `workflow/api-contract` (方針)
- `workflow/threat-model` (セキュリティ①)
- `common/visual-design` (UI 案件)
- `integration/agent-design` / `integration/agent-cost-design` (AI agent 案件)

## アンチパターン

- ❌ ADR snapshot を後追いで起票 (PLAN-156/PLAN-224 で発覚した V-model 違反、本工程で先に起票)
- ❌ tl-advisor 召喚 skip (G4 blocking 対象)
- ❌ 総合テスト設計のペア凍結を skip (V-model 違反、L9 総合テスト工程が空回り)
- ❌ アーキテクチャ doc を PLAN.md 内に書く (PLAN は L7 のみ、本工程は doc + ADR が成果物)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L4-basic-design.md](../../../HELIX-workflows/helix-process/L4-basic-design.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ） |
| 入力 | L3 要件定義 |
| 出力 | L5 詳細設計 への入力 |
| ペアとなるテスト設計 | 総合テスト設計（右腕 L9 総合テストで実行） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L4-方式設計plan`
- システム構成
- アーキテクチャ
- 技術スタック

### `L4-機能設計plan`
- 機能構成
- 機能間連携

### `L4-画面設計plan`
- 画面レイアウト確定
- 画面項目定義

### `L4-データ設計plan`
- 論理データモデル
- テーブル概要
- ER図

### `L4-外部IF設計plan`
- 外部システム連携
- API 概要

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

