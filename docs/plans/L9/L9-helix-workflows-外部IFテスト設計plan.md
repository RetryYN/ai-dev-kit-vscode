---
plan_id: L9-helix-workflows-外部IFテスト設計plan
title: "L9-helix-workflows-外部IFテスト設計plan: HELIX-workflows V2 外部IF総合テスト設計 (L4 外部IF設計 pair)"
kind: design
layer: L9
drive: be
status: draft
created: 2026-05-28
owner: PM
process_layer: L9
parent_process: HELIX-workflows/helix-process/L9-system-test.md
pairs_design:
  - docs/v2/L4-architecture/helix-workflows-interface-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G9 evidence)"
  - role: qa
    slot_label: "QA — 総合テスト設計"
generates:
  - artifact_path: docs/v2/L9-test-design/helix-workflows-interface-test-design.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-外部IF設計plan
  requires:
    - L4-helix-workflows-外部IF設計plan
  blocks: []
sibling_adr:
  - ADR-044 (V2 architecture snapshot)
  - ADR-042 (recommended command)
  - ADR-047 (Reverse Gateway Profile wiring)
related_docs:
  - HELIX-workflows/helix-process/L9-system-test.md
  - docs/v2/L4-architecture/helix-workflows-interface-design.md
---

# L9-helix-workflows-外部IFテスト設計plan: HELIX-workflows V2 外部IF総合テスト設計 (L4 外部IF設計 pair)

> **工程**: L9 (L4 外部IF設計 pair freeze)
> **正本**: HELIX-workflows/helix-process/L9-system-test.md
> **本 PLAN の対象**: L4 外部IF設計 doc (CLI 36 / hook 仕様 / route_engine 契約 v2) に対する総合テスト設計を起票する。

## §0 PLAN concept

V-model L4↔L9 pair freeze の対側として、L4 外部IF設計 doc の CLI 統一 36 件 / route_engine v2 契約 (ADR-042/047) を総合テスト設計として ratchet する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | L4 外部IF設計 doc 精読 | ☐ pending |
| 2 | 総合テスト設計 doc 起草 | ☐ pending |
| 3 | tl-advisor adversarial check (G9 evidence) | ☐ pending |
| 4 | doc-reviewer 品質レビュー | ☐ pending |
| 5 | PM finalize + status: completed | ☐ pending |

## §2 検証対象 (skeleton)

- CLI 36 件統一の正常系・異常系
- route_engine v2 契約 (gateway / forward_target / recommended_pipeline)
- ADR-042 recommended_command backward compat
- ADR-047 Reverse Gateway Profile 経由 routing

## §3 受入条件 (DoD)

- 総合テスト設計 doc 起草完了
- L4 外部IF設計 doc との双方向 trace 確立

## §4 carry

- skeleton。本体起草は Wave 6 (route_engine 契約拡張) 後に Wave 8 で実施。
