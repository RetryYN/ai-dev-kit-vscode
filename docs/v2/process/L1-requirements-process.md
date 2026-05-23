---
doc_id: process-L1-requirements
title: "L1 要件定義工程の進め方"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L1
pairs_with_test_phase: L8
---

# L1 要件定義工程の進め方

## 入力

- ユーザー要望 (チャット / 企画書 draft)
- 既存 docs/v2/L1-REQUIREMENTS.md (継続改訂時)
- 業界 standard (IPA 非機能要求グレード 2018 / ISO/IEC 25010 / OWASP 等)
- skill: `workflow/requirements-handover` / `workflow/requirements-deriver` / `workflow/doc-system-architect`

## 進め方

### Step 1: 要件抽出
- ユーザー要望を **機能要件 (FR)** / **ビジネス要件 (BR)** / **非機能要件 (NFR)** に分類
- 曖昧な点は `workflow/requirements-handover` skill で **確認 protocol** を回す (人間確認必須)

### Step 2: 非機能要件の機械的導出
- `workflow/requirements-deriver` skill で **R1-R14 シグナル** (複数/顧客/組織/テナント/SaaS/決済/個人情報/連携/24時間/大量 等) を機能要件から抽出
- IPA 非機能要求グレード 2018 (6 大項目) × ISO/IEC 25010 (8 特性) の二軸タグ付け
- 分離レベル / 冗長構成 / 認証方式まで展開

### Step 3: 業界 standard 整合
- PLAN-087 ガード遵守 (Web 検索 3 query 必須、IPA / ISO / OWASP / 業界事例)
- 検索結果を `docs/v2/L1-REQUIREMENTS.md` 内 references section に転記

### Step 4: 受入条件 (acceptance criteria) 確定
- 各 FR / BR / NFR に対応する **L8 受入テスト設計** とペア凍結
- ペアは V-model 4 artifact ① (要件 doc) ↔ ③ (L8 受入テスト設計 doc) の双方向 trace

### Step 5: G1 ゲート通過判定
- `skills/tools/ai-coding/references/gate-policy.md` の G1 条件を満たすことを確認
- 不足あれば前 Step に戻る

## 成果物

- **正本**: `docs/v2/L1-REQUIREMENTS.md` (FR-* / BR-* / NFR-* / AC-* の番号付き列挙)
- **ペア artifact**: `docs/v2/L4-test-design/L8-*-acceptance-test-design.md` (受入テスト設計)
- **トレーサビリティ**: `helix.db.requirements` table への自動登録 (`helix req add` 経由、V5 framework 完遂後)

## PLAN は出力しない

L1 要件定義工程の成果物は **doc のみ**。PLAN は L4 実装工程まで出てこない。要件定義をスキップして PLAN を起票するのは V-model 違反。

## ゲート

- **G1 (要件完了ゲート)**: PM + PO 判定、`skills/tools/ai-coding/references/gate-policy.md` 参照
- **G0.5 (企画突合ゲート、本 PR で前段)**: 企画書の全項目が L1 に反映されているか PM 判定

## 関連 skill

- `workflow/requirements-handover` (確認 protocol)
- `workflow/requirements-deriver` (R1-R14 シグナル + NFR 機械導出)
- `workflow/doc-system-architect` (ドキュメント体系メタ設計)
- `workflow/verification` (受入条件 ↔ 受入テスト設計の対応検証)

## アンチパターン

- ❌ PLAN を先に起票して、後から要件 doc を逆引きする (PLAN 主導は V-model 違反)
- ❌ 要件定義を skip して L2 全体設計に進む (設計が要件から派生しない)
- ❌ 受入条件 (AC) を書かずに G1 を通す (L8 受入工程でペア検証不能)
