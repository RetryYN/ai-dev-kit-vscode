---
doc_id: process-L2-design
title: "L2 全体設計工程の進め方"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L2
pairs_with_test_phase: L6
---

# L2 全体設計工程の進め方

## 入力

- `docs/v2/L1-REQUIREMENTS.md` (L1 工程の成果物、必須)
- 既存 ADR (`docs/adr/ADR-*.md`)
- 既存 L2 doc (`docs/v2/L2-MASTER.md` / `docs/v2/CONCEPT.md`)
- skill: `workflow/design-doc` / `workflow/adversarial-review` / `workflow/api-contract` (方針) / `common/visual-design` (UI 案件)

## 進め方

### Step 1: 大局判断の抽出
- L1 要件 (FR / BR / NFR / AC) から **大局判断が必要な技術選択** を抽出
- 例: アーキテクチャパターン採用 / DB 物理分離 / framework 採用 / 認証方式 等

### Step 2: ADR snapshot 起票判定
- 大局判断あり → **ADR snapshot 起票必須** (新規 `docs/adr/ADR-NNN-<topic>.md`)
- 大局判断なし → 既存 L2 doc に統合のみ
- 判定基準: `[[feedback_adr_before_plan_violation]]` の「PLAN tree 内 L2 大局判断あり → ADR snapshot 必須」原則 (本工程では PLAN tree 不在でも ADR は L1 要件から直接派生)

### Step 3: 業界 standard 整合 + tl-advisor adversarial check
- PLAN-087 ガード遵守 (Web 検索 3 query 必須)
- **tl-advisor 召喚** (`helix codex --role tl-advisor`) で設計妥当性 + corner case 確認 (mandatory、本工程の核)
- changes_required 判定なら全 P0/P1 反映後に再召喚

### Step 4: 設計とテスト設計のペア凍結
- L2 全体設計 ↔ L6 統合テスト設計 を **同一スプリント内でペア凍結** (CONCEPT.md §5 line 304-309)
- L6 統合テスト設計は `docs/v2/L4-test-design/L6-*-system-test-design.md` (V-model 4 artifact ③)

### Step 5: G2 ゲート通過判定
- adversarial-review 結果 + ペア凍結確認 + セキュリティ① で gate-policy.md §G2 通過

## 成果物

- **正本**: `docs/v2/L2-MASTER.md` (全体設計の指針 + 大局判断履歴) / `docs/v2/CONCEPT.md` (企画書) / `docs/adr/ADR-*.md` (個別 snapshot)
- **ペア artifact**: `docs/v2/L4-test-design/L6-*-system-test-design.md` (統合テスト設計)
- **トレーサビリティ**: `helix.db.design_decisions` table (V5 framework 完遂後)

## PLAN は出力しない

L2 全体設計工程の成果物は **doc + ADR のみ**。PLAN は L4 実装工程まで出てこない。

## ゲート

- **G2 (設計凍結ゲート)**: TL + PM 判定、adversarial-review + ミニレトロ + セキュリティ① + V-model 統合テスト設計ペア凍結
- bypass 禁止: `HELIX_ALLOW_NO_ADVERSARIAL=1` + 理由 evidence 必須

## 関連 skill

- `workflow/design-doc` (設計 doc 作成手順)
- `workflow/adversarial-review` (tl-advisor 召喚判断、本工程の mandatory)
- `workflow/threat-model` (G2 セキュリティ①)
- `common/security`
- `workflow/api-contract` / `workflow/dependency-map` (Phase 1 方針)

## アンチパターン

- ❌ ADR を PLAN から後追いで起票 (PLAN-156 / PLAN-224 で発覚した V-model 違反、本工程で L1 派生として先に起票すべき)
- ❌ tl-advisor 召喚 skip (G2 ゲート blocking 対象、advisor_session_id 必須)
- ❌ L2 設計 doc を PLAN.md 内に埋め込む (PLAN 単位で設計が散在、再利用不能)
- ❌ L6 統合テスト設計とのペア凍結を後回し (V-model 違反)
