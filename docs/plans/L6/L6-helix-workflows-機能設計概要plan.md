---
plan_id: L6-helix-workflows-機能設計概要plan
title: "L6-helix-workflows-機能設計概要plan: HELIX-workflows V2 機能設計上位概念 (L7 機能 PLAN 群の親)"
kind: design
layer: L6
drive: be
status: draft
created: 2026-05-28
owner: PM
process_layer: L6
parent_process: HELIX-workflows/helix-process/L6-functional-design.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check"
generates:
  - artifact_path: docs/v2/L6-functional-design/helix-workflows-functional-overview.md
    artifact_type: design_doc
dependencies:
  parent: L5-helix-workflows-外部IF詳細設計plan
  requires:
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
  blocks:
    - L7-helix-workflows-(機能名)-implplan (機能ごとに別 PLAN、本 PLAN の子)
sibling_adr:
  - ADR-044 (V2 architecture snapshot)
  - ADR-045 (F6-F10 governance snapshot)
  - ADR-047 (Reverse Gateway Profile wiring)
related_docs:
  - HELIX-workflows/helix-process/L6-functional-design.md
  - docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
---

# L6-helix-workflows-機能設計概要plan: HELIX-workflows V2 機能設計上位概念

> **工程**: L6 (機能設計、上位概念)
> **正本**: HELIX-workflows/helix-process/L6-functional-design.md
> **本 PLAN の対象**: HELIX-workflows V2 の機能設計 (endpoint / 関数 schema 単位) の **上位概念** PLAN。各機能ごとの L6-helix-workflows-<機能名>-functional-designplan は本 PLAN の子として別途起票される。L7 実装 PLAN (`L7-cli-helix-*-implplan` 等多数既存) の親に相当する。

## §0 PLAN concept

V-model L6↔L7 pair freeze の上位概念として、HELIX-workflows V2 が扱う機能 (mode 別 routing / CLI 36 件 / hook / route_engine 等) の機能設計を統括する PLAN。各機能の具体的 schema / endpoint / 関数 signature は子 PLAN (L6-<機能名>-functional-designplan) で個別に凍結する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | HELIX-workflows V2 機能一覧 (F1-F10) の機能設計優先順位決定 | ☐ pending |
| 2 | 機能設計子 PLAN 起票方針 (1 機能 1 PLAN or 1 領域 1 PLAN) | ☐ pending |
| 3 | 既存 L7 implplan との trace 整合 (本 PLAN の子として再分類) | ☐ pending |
| 4 | 子 PLAN 起票 (機能数に応じて N 件) | ☐ pending |
| 5 | tl-advisor adversarial check | ☐ pending |
| 6 | PM finalize + status: completed | ☐ pending |

## §2 子 PLAN candidate (skeleton)

ADR-045 F6-F10 governance snapshot の F6-F10 に対応する子 PLAN を想定:

- L6-helix-workflows-F6-routingplan (route_engine v2 機能設計)
- L6-helix-workflows-F7-validationplan (helix doctor 機能設計)
- L6-helix-workflows-F8-handoverplan (handover 機能設計)
- L6-helix-workflows-F9-budgetplan (budget 機能設計)
- L6-helix-workflows-F10-skill-radarplan (skill radar 機能設計)

他に Reverse Gateway Profile 経路 / mode 別 CLI / deviation log handler 等。

## §3 受入条件 (DoD)

- 機能設計上位概念 doc 起草完了 (docs/v2/L6-functional-design/helix-workflows-functional-overview.md)
- 子 PLAN 起票方針 確定
- L5 詳細設計 4 PLAN との双方向 trace 確立
- L7 implplan 群との親子関係明示

## §4 carry

- 本 PLAN は **HELIX-workflows V2 L6↔L7 pair freeze の片肺解消のための上位概念 skeleton 起票** (2026-05-28 ユーザー指摘で確立)
- 子 PLAN (L6-<機能名>-functional-designplan) の起票は次 wave carry
- 既存 L7 implplan 群 (cli-helix-recovery / refactor / retrofit / route 等) との trace 整合も次 wave
