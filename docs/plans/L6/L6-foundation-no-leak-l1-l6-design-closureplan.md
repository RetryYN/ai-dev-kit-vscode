---
plan_id: L6-foundation-no-leak-l1-l6-design-closure
title: "L1-L6 foundation/no-leak 設計クローズ (UT-anchor, closure ledger)"
kind: function-design
layer: L6
process_layer: L6
drive: be
status: completed
tl_review: approve  # tl-advisor 再レビュー 2026-06-21 = approve / P0 none / P1 none (.helix/tasks/tl-rereview-l1l6-closure.md)
created: 2026-06-21
owner: PM
forward_return: "L1-L6 Forward 設計層 (F2=L4↔L9/L5↔L8/L6↔L7, F1=G正本 db-auto-registration §F1, F3=review_evidence in-place)。UT-TDD adoption Process の foundation 設計を Forward へ収束。形式 status:frozen flip は follow-up gate ceremony。"
agent_slots:
  - role: pmo-sonnet
    slot_label: "偵察: UT 採用項目の L 層別抽出 / V2 doc 現状 / draft freeze blocker / Process 義務"
  - role: tl-advisor
    slot_label: "戦略諮問 (scope/F1F3 home/freeze gating) + 再レビュー (P0/P1=0, frozen 可否)"
generates:
  - artifact_path: docs/v2/audit/2026-06-21-l1-l6-design-closure-ledger.yaml
    artifact_type: markdown_doc
  - artifact_path: docs/v2/L1-requirements/helix-workflows-verification-strategy.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L3-requirements/helix-workflows-functional-registry.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L5-detailed-design/db-backed-evidence-lifecycle-詳細設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L6-functional-design/requirement-drift-機能設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L7-test-design/requirement-drift-単体テスト設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L7-test-design/deferred-gate-adoption-単体テスト設計.md
    artifact_type: doc_update
pairs_with:
  - L7
dependencies:
  parent: process-2026-06-21-ut-tdd-adoption-machine-precision
  requires: []
  blocks: []
related_docs:
  - docs/research/ut-tdd-fork-adoption-research-memo.md
  - docs/research/2026-06-21-no-leak-foundation-design-review.md
---

# L1-L6 foundation/no-leak 設計クローズ Plan

## Purpose

ユーザー /goal「L1 から L6 まですべて対応して設計の完全クローズまで。ぬけもれは絶対に許さない。UT ハーネスの調査レポートを見ながらまとめ上げること」への対応 PLAN。UT-TDD fork 調査レポート（[research-memo](../../research/ut-tdd-fork-adoption-research-memo.md) / [no-leak design-review](../../research/2026-06-21-no-leak-foundation-design-review.md)）を正本参照し、V-model 左腕 L1-L6 の foundation/no-leak 設計を全層クローズする。L6 を representative layer として起票するが、対象は L1-L6 横断（F1/F2/F3 + requirement-drift + 検証戦略 + 機能 registry）。

絶対原則「workflow の成果は対応する PLAN として起票し Forward へ収束」の履行として、本クローズを PLAN 化する（G-review が要求する V モデル紐付け）。

## Scope（closure ledger に機械計数で帰属）

正本 = [docs/v2/audit/2026-06-21-l1-l6-design-closure-ledger.yaml](../../v2/audit/2026-06-21-l1-l6-design-closure-ledger.yaml)。全 UT-anchor 23 項目を `closed(8) / closed_via_g_reference(1) / explicitly_deferred(8) / deferred_escalation(5) / out_of_scope(1)` に漏れなく帰属（silent omission ゼロ）。

- **closed**: F2 L4/L5/L6（F3 review_evidence in-place 相乗り）/ requirement-drift L6+L7 / L1 検証戦略 / L3 機能 registry / L7 deferred-gate-adoption。
- **closed_via_g_reference**: F1（G 正本 `db-auto-registration.md §F1`、V2 は trace 参照）。
- **explicitly_deferred**: F2-L7-pair（feature-ticketed 機械契約）/ UT #1/#3/#5/#6/#7/#9 / right-arm-execution-gates（GOAL-C 依存）。
- **deferred_escalation**: security NFR / runtime Loop3 / reviewer-calibration / concurrency-contract / telemetry-schema（人間確認・観測待ち）。
- **out_of_scope**: harness-external-tools-impact（別 owner TL）。

## 全て in-place（新規 design doc ゼロ = cascade 回避）

新 V2 design doc を作らず既存 doc を in-place 編集（asset-inventory / reference-integrity / ratification の count-pin cascade と G-P drift を回避、TL ruling 2026-06-21）。

## 重要な自己訂正

F2 の L6↔L7 pair を埋めるため L7 test design doc を新設して closed 化を試みたが、機械契約 `test_helix_l0_l14_flow_contract`（`assert not L7_TEST_DESIGN.exists()` + `design_gap_status=L4_L6_closed_L7_feature_ticketed`）が「L7 = add-feature 境界＝作らない」を pin していると baseline stash 比較で判明 → L7 doc を revert 削除し explicitly_deferred（feature-ticketed）に再分類。機械契約は TL 助言に優先する。

## Acceptance

- closure ledger が全 UT-anchor 項目を 3 区分（closed / deferred / out）に漏れなく帰属し、宣言 count と実 row 数が機械一致（23）。
- 全 in-place 編集が verification green: flow contract 89 passed / 回帰 163 passed / detector 29 passed / doctor bats 24 passed / vg_overview overall_clean=True（required_clean 全 12 subcheck）/ requirement_drift blocking_clean。
- tl-advisor 戦略諮問 + 再レビュー approve（P0/P1=0）。
- 各 doc に `freeze_readiness: design_closed_tl_rereviewed_approve_2026_06_21` marker。

## Result

設計クローズ達成（本文完成 + pair 帰属 + TL approve + 全 detector green）。形式的 `status: draft -> frozen` flip は `vmodel_pair_freeze` 厳格化 + status-pin テスト破壊回避のため follow-up gate ceremony へ分離（ledger `freeze_state` に記録）。実装（F1 Reverse→Add-feature / F2 Add-feature+ADR / 各 detector）は GOAL-C 着地後に別 PLAN。
