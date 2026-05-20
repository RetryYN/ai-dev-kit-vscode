---
plan_id: PLAN-NNN-research-slug
title: "PLAN-NNN: (調査タイトル placeholder)"
kind: research
layer: L1
drive: be
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: research
    slot_label: "Research — 一次情報収集・エビデンス整理"
  - role: pmo-tech-docs
    slot_label: "PMO-Tech-Docs — 外部ドキュメント精読"
generates:
  - artifact_path: docs/research/<slug>-research-memo.md
    artifact_type: markdown_doc
  - artifact_path: docs/adr/ADR-NNN-<slug>.md
    artifact_type: adr_snapshot
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
L2 設計判断に先立ち、一次情報に基づく調査結果を PLAN routing 可能な形で構造化する。

## §1 目的
仮説ベースでなく一次ソースベースの知見を収集し、ADR / PLAN 起票の根拠を明確化する。

## §2 背景
過去の実装起票で調査不足由来の逸脱が発生したため、research kind を明示化して再発を防ぐ。

## §3 実装計画
### 質問定義
- 何を知りたいかを 5W1H で固定し、検証対象を明確化。

### Web 検索 3 query
- Query 1: `HELIX PLAN テンプレート kind design impl poc reverse troubleshoot refactor retrofit research add-design add-impl recovery`
- Query 2: `V-model 4 artifact 双方向 trace 設計 テスト設計 implementation`
- Query 3: `PLAN-091 エンベッド設計 PLAN embed workflow`

### 一次ソース精読
- 公式/正本文書を優先し、要件の同一文言を抜き出して引用記録する。

### ADR 起票判断
- 調査結果が規約変更・ルール追加を要する場合は ADR 起票を推奨。

### PLAN routing
- 調査結果から実施すべき PLAN kind と優先順を確定し、次の L2/L3 へ接続。

## §4 受入条件 / DoD
- 質問定義から PLAN routing までの一貫性がある。
- 3 query が記録され、一次ソースの参照が追跡可能。
- ADR 判定（要/不要）が明記。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-021〜ADR-024（該当時）
- docs: `helix/HELIX_CORE.md`, `skills/workflow/design-doc/SKILL.md`, `skills/workflow/api-contract/SKILL.md`
