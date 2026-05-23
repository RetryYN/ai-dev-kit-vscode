---
doc_id: process-L01
title: "L1 要求定義 + 運用テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L1
pairs_with: L14
canonical_source: HELIX-workflows/helix-process/L1-requirements.md
---

# L1 要求定義 + 運用テスト設計

## 入力

- L0 企画書 (必須)
- 業界 standard (IPA 非機能要求グレード 2018 / ISO/IEC 25010)
- skill: `workflow/requirements-handover` / `workflow/requirements-deriver`

## 進め方

### Step 1: 業務要求 (Business Requirements) の抽出
- 企画書から **業務要求** (BR) を抽出 (誰が / 何のために / どんな業務で使うか)
- 「機能要件」より上位の **ビジネス目標 + ユーザーゴール**

### Step 2: 運用シナリオ + 非機能要求の整理
- R1-R14 シグナル (`workflow/requirements-deriver`) で非機能要求 (NFR) を機械導出
- IPA × ISO 25010 二軸タグ付け

### Step 3: 運用テスト設計のペア凍結 (V-model L14 ペア)
- 業務要求ごとに **運用テスト** (どう運用フェーズで検証するか) を設計
- `docs/v2/L14-test-design/<area>-operational-test-design.md` に pair として書く

### Step 4: G1 要求定義ゲート通過判定
- 業務要求 + NFR + 運用テスト設計 ペア凍結を PM + PO 判定

## 成果物

- **正本**: `docs/v2/L1-requirements/business-requirements.md` (BR-* / NFR-*)
- **ペア artifact**: `docs/v2/L14-test-design/<area>-operational-test-design.md` (運用テスト設計)
- **トレーサビリティ**: helix.db.requirements (V5 framework 完遂後)

## ペア凍結相手

L14 運用検証 + 機能改善

## ゲート

- **G1 要求定義ゲート**: PM + PO 判定

## 関連 skill

- `workflow/requirements-handover` (確認 protocol)
- `workflow/requirements-deriver` (R1-R14 / NFR 機械導出)
- `workflow/doc-system-architect` (ドキュメント体系)

## アンチパターン

- ❌ PLAN を起票する (L1 では PLAN 起票しない、doc のみ)
- ❌ 運用テスト設計のペア凍結を skip (L14 で運用検証が空回り)
- ❌ システム要件 (FR) に飛び込む (本工程は業務要求まで、FR は L3 で)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 左腕（設計フェーズ） |
| 入力 | L0 企画書 |
| 出力 | L3 要件定義 への入力 |
| ペアとなるテスト設計 | 運用テスト設計（右腕 L14 運用検証で実行） |

### この工程の PLAN (HELIX-workflows 正本)

PLAN は機能（ドキュメント）単位で起票し、工程表（作成手順＋進捗）と実装計画を内蔵する。

### `L1-業務要求plan`
- 目的・背景（WHY / WHAT / WHO）
- 対象業務一覧
- 業務フロー
- ステークホルダー
- 現状課題とあるべき姿

### `L1-機能要求plan`
- 機能一覧
- 利用シナリオ（ユースケース）
- 操作とデータの流れ
- 入出力

### `L1-画面要求plan`
- 画面一覧
- 画面遷移の要望
- 表示・操作への要望
- （具体的な画面設計は L2）

### `L1-技術要求plan`
- 採用技術・技術制約
- 外部連携 / インターフェース要望
- 既存システム制約

### `L1-非機能要求plan`
- 可用性
- 性能・拡張性
- 運用・保守性
- 移行性
- セキュリティ
- システム環境・エコロジー
- （IPA 非機能要求グレード 6大項目に準拠）

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

