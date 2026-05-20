---
plan_id: PLAN-NNN-retrofit-slug
title: "PLAN-NNN: (retrofit タイトル placeholder)"
kind: retrofit
layer: cross
drive: be
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: docs
    slot_label: "Docs — ドキュメント規約適合更新"
  - role: pmo-sonnet
    slot_label: "PMO — 整合確認・差分チェック"
generates:
  - artifact_path: docs/plans/<slug>-retrofit-matrix.md
    artifact_type: markdown_doc
  - artifact_path: cli/config/<slug>.yaml
    artifact_type: yaml_config
dependencies:
  parent: PLAN-091
  requires: []
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
既存文書/コード資産を新規標準へ適合させるため、PLAN 形式・参照・規約の retrofit を明文化する。

## §1 目的
改訂標準に対して差分を可視化し、段階 rollout で安全に移行する。

## §2 背景
既存資産の種別/参照/命名差異により、運用時に検索・監査・trace が困難になっている。

## §3 実装計画
### 既存 doc/code 一覧
- 対象資産をカテゴリ別に洗い出し、対象外を明示。

### 規約適用範囲
- 変更すべき規約（frontmatter、§構造、参照ルール）を範囲別に定義。

### 差分プレビュー
- 差分影響が大きい順に preview を作成し、優先度を明示。

### 段階 rollout
- 低リスク→中リスク→高リスクの順で適用し、各段で受入確認を行う。

## §4 受入条件 / DoD
- 対象一覧、適用範囲、rollout順がすべて記録。
- 差分を伴う項目ごとに受入結果と保留理由を記載。
- `kind: retrofit` 前提の Step がテンプレート内で順守。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-024
- docs: `helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`, `cli/ROLE_MAP.md`, `docs/commands/index.md`
