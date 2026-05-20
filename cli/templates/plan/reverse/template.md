---
plan_id: PLAN-NNN-reverse-slug
title: "PLAN-NNN: (逆引き設計タイトル placeholder)"
kind: reverse
layer: cross
drive: reverse
workflow_phase: R1
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計復元・adversarial check"
  - role: research
    slot_label: "Research — コード・設定・運用実態の証拠収集"
generates:
  - artifact_path: docs/reverse/<slug>-evidence.md
    artifact_type: markdown_doc
  - artifact_path: docs/design/<slug>-as-is-design.md
    artifact_type: design_doc
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
既存状態からの復元設計を逆引きし、PLAN-091 の実施前提として R0〜R4 を一本化する。

## §1 目的
証拠に基づき設計と意図を再構築し、Forward へ接続可能なギャップ一覧を作成する。

## §2 背景
実体の不一致がある資産を前提に、Reverse で収集した事実を設計/実装へ接続するための段取りが必要。

## §3 実装計画
### R0: Evidence Acquisition
- コード、設定、運用ログ、実行記録を収集し、観測可能な事実のみ採録。

### R1: Observed Contracts
- 実 API / DB / I/O 契約を観測ベースで抽出し、未確定要件を未仮定化。

### R2: As-Is Design
- 観測契約から現状設計の構造を復元し、欠落箇所を可視化。

### R3: Intent Hypotheses
- 仕様者意図の仮説を列挙し、検証可否と危険度を重み付けする。

### R4: Gap & Routing (Forward 接続)
- Gaps を L1-L4 / L5-L6 への Forward ルートに変換し、次アクションと所有者を明示。

## §4 受入条件 / DoD
- R0〜R4 の証拠・根拠・未確定事項が記録されている。
- `forward routing` が具体的な PLAN-ids / DoD と結びついている。
- `kind: reverse` を保持し、§0〜§5 完備。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-022（逆引き救済方針）, ADR-023（fail-close 手順）
- docs: `helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`, `docs/commands/scrum.md`
