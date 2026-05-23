---
doc_id: process-L03
title: "L3 要件定義 + 受入テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L3
pairs_with: L12
canonical_source: HELIX-workflows/helix-process/L3-requirements-definition.md
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

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ） |
| 入力 | L1 要求定義・L2 画面設計 |
| 出力 | L4 基本設計 への入力 |
| ペアとなるテスト設計 | 受け入れテスト設計（右腕 L12 受入テストで実行） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L3-業務要件plan`
- 業務フロー（確定版）
- 業務ルール
- 対象業務範囲

### `L3-機能要件plan`
- 機能一覧（確定版）
- 機能仕様
- 入出力定義

### `L3-非機能要件plan`
- 可用性 / 性能・拡張性 / 運用・保守性 / 移行性 / セキュリティ / システム環境
- （IPA 非機能要求グレードのグレード値で確定）

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

