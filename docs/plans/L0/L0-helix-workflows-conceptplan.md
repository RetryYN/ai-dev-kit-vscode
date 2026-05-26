---
plan_id: L0-helix-workflows-conceptplan
title: "L0-helix-workflows-conceptplan: HELIX-workflows 見直し企画書"
kind: planning
layer: L0
drive: be
status: draft
created: 2026-05-26
owner: PM
process_layer: L0
parent_process: HELIX-workflows/helix-process/L0-concept.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
generates:
  - artifact_path: docs/v2/L0-helix-workflows/concept.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires: []
  blocks:
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
related_docs:
  - HELIX-workflows/helix-process/L0-concept.md
  - docs/v2/process/L00-planning.md
---

## §0 PLAN concept

> **工程**: L0 (ペア凍結なし)
> **正本**: HELIX-workflows/helix-process/L0-concept.md
> **本 PLAN の対象**: 既存の **HELIX-workflows** (2026-05-24 V2 完全移行で正本宣言された「道」、47 doc / L0-L14 工程定義 / 9 mode workflow / 工程専門 2 / 管理・自動化基盤 21) を素材として、**見直し企画書**を起票する。HELIX-workflows の現状到達点 / 残課題 / 次工程 (L1 要求定義) への接続方針を整理する見直し工程。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 素材調査: HELIX-workflows 47 doc 全体構造把握 + 主要 doc (L0-concept / L00-planning / template / layer-context-injection / cross-cutting / integration-map / automation-gate-map) 精読 | ☑ completed (2026-05-26) |
| 2 | 現状到達点と残課題の棚卸し (PLAN dir 整備状況 / 4 artifact trace warn / pair freeze warn / mode 接続 trace / helix doctor warn / dogfooding 状況) | ☑ completed (2026-05-26) |
| 3 | G0.5 前段 adversarial check (pdm-innovation-manager 内で tl-advisor 1 回呼ぶ) | ☑ completed (2026-05-26、conditional approve) |
| 4 | 製本対象 doc `docs/v2/L0-helix-workflows/concept.md` 起草 (6 必須項目: 背景・目的 / 解決する課題 / スコープ / 投資対効果 / 成功条件 / 想定リスク) | ☑ completed (2026-05-26) |
| 5 | tl-advisor adversarial check (G0.5 evidence、1 回必須、HELIX-workflows 規約) | ☑ completed (2026-05-26、判定: blocked → P0 1 件 + P1 4 件 + P2 2 件 carry を返却) |
| 6 | TL レビュー結果反映 (P0 量閉じ式向き訂正 / P1#2 gate 機械判定境界分解 / P1#3 V モデル DB 10 core + view 区分明示 / P1#4 Diagram 2 Incident/Recovery 分岐粒度 / P1#5 AC-07 実数訂正 + AC-09/10/11 追加 / P2 L2/L10 unskip 条件 + Phase α 3 層分割案) | ☑ completed (2026-05-26、5 件 + carry 2 件 全反映) |
| 7 | pmo-sonnet 再 audit (反映漏れ / 二次 drift / AC 充足 / 残 carry 妥当性) | ☑ completed (2026-05-26、判定: yes_with_minor、反映漏れ 0、二次 drift D1 = §6.5.6 line 513 blockquote `1 個` → `7 個`、D2 = G7 AI 判定境界の L1 carry) |
| 8 | D1 修正 (§6.5.6 line 513 blockquote `1 個` → `7 個`、AC-11 完全充足化) | ☑ completed (2026-05-26、1 行修正) |
| 9 | G0.5 ゲート判定再評価 (conditional_approve 取得 → ユーザー判断) | ☑ completed (2026-05-26、conditional_approve 取得 + ユーザー approve、L0 commit 9d65a63 push 完了 4428aa5..cd598d2) |
| 10 | L1 接続 (`L1-helix-workflows-<area>plan` 4 種 + L14-test-design pair artifact + 4 製本 doc 同時起票、画面要求は L2 skip により対象外) | ☑ completed (2026-05-26、Phase A Opus 業務要求 + Phase B Codex SE 3 並列 + Phase C pmo audit yes_with_minor + Phase C.1 修正 3 件 + Phase D tl-advisor blocked → P0/P1 6 件修正 + Phase D.1 pmo 2nd yes_with_minor + Phase D.2 1 行修正 ×2 → G1 conditional_approve 取得、commit aa86a22 push 完遂) |
| 11 | L3 接続 (`L3-helix-workflows-<area>要件plan` 3 種 + L12-test-design pair artifact + 3 製本 doc 同時起票、技術要求は機能要件の入出力に統合) | ☑ completed (2026-05-26、Phase E.A Opus 業務要件 + Phase E.B Codex SE 2 並列 機能/非機能要件 + Phase E.B.1 L12 §2/§3 一括適用 (AC-FR 14 + AC-NFR 25) + Phase E.C pmo 1st yes_with_minor + Phase E.C.1 修正 4 件 + Phase E.D tl-advisor blocked → P0/P1 5 件修正 + Phase E.D.1 pmo 2nd yes_with_minor + Phase E.D.2 1 行修正 → G3 conditional_approve 取得) |
| 12 | L4 接続 (`L4-helix-workflows-基本設計plan` + L9-test-design 総合テスト設計 pair artifact、L4↔L9 pair freeze、L1-IN-14 team 構造確定) | □ pending (次 session 候補) |

## §2 実装計画 (記載項目をどう埋めるか)

### この工程で起票する PLAN 群

- `L0-helix-workflows-conceptplan` (本 PLAN): HELIX-workflows 見直し企画書

### 各 PLAN の記載項目

詳細は [HELIX-workflows/helix-process/L0-concept.md](../../../HELIX-workflows/helix-process/L0-concept.md) §この工程の PLAN を参照。製本対象 doc に以下 6 項目を必須記載:

- 背景・目的
- 解決する課題
- スコープ (対象 / 対象外)
- 投資対効果
- 成功条件・KGI / KPI
- 想定リスク

## §3 成果物

- **製本対象 doc**: [`docs/v2/L0-helix-workflows/concept.md`](../../v2/L0-helix-workflows/concept.md) (本 PLAN が完成させる正本)
- **HELIX-workflows 正本 (素材)**: [HELIX-workflows/helix-process/L0-concept.md](../../../HELIX-workflows/helix-process/L0-concept.md)
- **ペア凍結**: なし (L0 はペア凍結なし、L11 総合レビューと緩いペア)

## §4 受入条件 / DoD

- [x] §1 工程表 Step 1-6 完了 (素材調査 / 棚卸 / tl-advisor adversarial check / 製本 doc 起草 / TL レビュー結果反映)
- [~] §1 工程表 Step 7 in_progress (pmo-sonnet 再 audit、結果待ち)
- [ ] §1 工程表 Step 8-9 完了 (G0.5 判定再評価 + L1 接続)
- [x] §2 実装計画の必須 6 項目 が製本 doc に記載 (背景 / 課題 / スコープ / 投資対効果 / 成功条件 / リスク + §6.5 Diagram 7 + §8 L1 バトン 17件 + §9 AC-01〜AC-11)
- [x] tl-advisor adversarial check 実施完了 (判定: blocked → 修正反映後 conditional_approve 見込み)
- [x] tl-advisor 指摘 P0 1 件 + P1 4 件 + P2 2 件 全件反映済 (§5.3 / §6.5.2 / §6.5.4 / §6.5.6 / §8 / §9)
- [ ] pmo-sonnet 再 audit pass (反映漏れ 0 / 二次 drift 0 / AC 全充足)
- [ ] G0.5 acceptance criteria 全 11 項目満足 (AC-01〜AC-11)
- [ ] L1 接続準備完了 (5 種 PLAN 起票 + L14-test-design pair artifact 同時起票、L14-test-design template skeleton 不在 carry あり)

## §5 関連 PLAN / ADR / docs

- **HELIX-workflows 正本**: HELIX-workflows/helix-process/L0-concept.md
- **工程 doc**: docs/v2/process/L00-planning.md
- **template**: cli/templates/plan/v2/L00-planning-template.md
- **L1 template (調査済)**: cli/templates/plan/v2/L01-requirements-template.md (5 種 PLAN 起票: 業務要求 / 機能要求 / 画面要求 / 技術要求 / 非機能要求)
- **L1 工程 doc**: docs/v2/process/L01-requirements-and-operational-test-design.md (L1↔L14 ペア凍結、L1 で運用テスト設計 skeleton 同時起票必要)
- **L14 正本**: HELIX-workflows/helix-process/L14-operation-verification.md
- **L14 工程 doc**: docs/v2/process/L14-operations-and-improvement.md
- **参考 (draft 凍結)**: docs/v2/CONCEPT.md (HELIX V2 初期企画書、is_reference 相当、見直し対象の前世代)
- **下流 PLAN**: `L1-helix-workflows-業務要求plan` / `L1-helix-workflows-機能要求plan` / `L1-helix-workflows-技術要求plan` / `L1-helix-workflows-非機能要求plan` (画面要求は L2/L10 skip により対象外、本 PLAN 完遂後に起票)
- **L14 pair artifact**: `docs/v2/L14-test-design/helix-workflows-operational-test-design.md` (L1 起票時に同時 skeleton 起票必要、L14-test-design 用 template 不在 carry)
- **tl-advisor evidence**: `.helix/tl-advisor-prompts/L0-helix-workflows-g05-review.md` (prompt) + tl-advisor 結果 (stdout log は session 終了時に破棄、要点は本 PLAN §1 Step 5/6 + concept.md §9 AC-09/10/11 に反映済)
