---
plan_id: PLAN-NNN-add-impl-slug
title: "PLAN-NNN: (実装追補タイトル placeholder)"
kind: add-impl
layer: L4
drive: be
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: se
    slot_label: "SE — 追加実装"
  - role: pmo-sonnet
    slot_label: "PMO — 整合確認・既存 trace チェック"
generates:
  - artifact_path: cli/lib/<module>.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_<module>.py
    artifact_type: test
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-NNN-impl
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
既存 PLAN 実装に対し追加機能を追記する場合の加筆実装計画を固定する。

## §1 目的
追加範囲を限定し、既存実装・既存テストとの整合を失わずに拡張する。

## §2 背景
既存テスト資産を再利用する前提で追加実装を行う場合、受入条件の再定義が必要。

## §3 実装計画
### 既存 PLAN 参照
- 対象 PLAN の現行実装・対象外範囲を確認し、差分対象を固定。

### 追加機能スコープ
- 追加機能を限定列挙し、非対応要件を明記。

### 既存テスト維持
- 既存テスト群を維持する方針を明示し、必要最小の更新だけに留める。

### 回帰確認
- 既存テスト＋追加対象テストを実行し、回帰リスクを数値で確認。

## §4 受入条件 / DoD
- 追加機能スコープが固定され、既存テスト方針が明記。
- 回帰確認により既存機能への影響が否定される。
- kind ごとの Step が埋まっている。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-024
- docs: `helix/HELIX_CORE.md`, `skills/workflow/design-doc/SKILL.md`, `docs/plans/`
