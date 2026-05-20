---
plan_id: PLAN-NNN-add-design-slug
title: "PLAN-NNN: (設計追補タイトル placeholder)"
kind: add-design
layer: L2
drive: be
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計追補判断・adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — 整合確認・双方向 reference 確認"
generates:
  - artifact_path: docs/design/<slug>-add-design.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-NNN-design
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
既存 PLAN に対する設計追補を、影響範囲を固定して増分更新するための加筆種別テンプレート。

## §1 目的
既存仕様を破壊せず、設計追補の理由・対象・参照更新を明確にする。

## §2 背景
既存 PLAN に情報が不足している状態で進行すると、実装時に同意形成不足や手戻りが発生する。

## §3 実装計画
### 既存 PLAN 参照
- 追補対象 PLAN を一意に特定し、差分前提を記載。

### 追補範囲
- 追加する設計内容（背景/要件/制約/テスト参照）を明確に分離。

### 既存 doc 整合
- 既存 docs との矛盾をチェックし、整合する表現に収斂。

### 双方向 reference 更新
- 元 PLAN と追補 PLAN の `関連 PLAN / ADR / docs` を相互参照として追加。

## §4 受入条件 / DoD
- 追補対象が明示され、対象外が明文化されている。
- 既存 doc との参照整合がとれている。
- 追加分が既存計画へ逆参照されること。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: 対象設計に関連する ADR
- docs: `helix/HELIX_CORE.md`, `skills/workflow/design-doc/SKILL.md`, `skills/SKILL_MAP.md`
