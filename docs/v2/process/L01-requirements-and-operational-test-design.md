---
doc_id: process-L01
title: "L1 要求定義 + 運用テスト設計"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L1
pairs_with: L14
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
