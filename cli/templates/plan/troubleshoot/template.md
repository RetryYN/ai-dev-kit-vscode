---
plan_id: PLAN-NNN-troubleshoot-slug
title: "PLAN-NNN: (障害対応タイトル placeholder)"
kind: troubleshoot
layer: L4
drive: troubleshoot
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: se
    slot_label: "SE — 修正実装"
  - role: qa
    slot_label: "QA — 回帰確認・再発防止検証"
generates:
  - artifact_path: cli/lib/<module>.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_<module>.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-NNN-incident-report.md
    artifact_type: doc_update
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-NNN-prereq
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
障害再現から修正・再発防止までの最短ルートを標準化し、同種インシデントの再発時に再利用可能な記録を残す。

## §1 目的
原因特定から修正実装までを文書主導で一貫化し、回帰確認までをテンプレート上で固定する。

## §2 背景
散在した原因メモにより、再発時に再現条件が失われる傾向があるため、PLAN 内で手順を定着する。

## §3 実装計画
### 再現手順
- 失敗条件（環境、入力、時刻、前提）を 1 回の最小手順で再現可能にする。

### 原因仮説
- 仮説を優先度順に3件以上置き、観測データで優先度を更新する。

### 修正
- 根本修正と回避策を分離し、実装変更は最小差分で反映する。

### 回帰確認
- 修正影響範囲のテスト再実行と監視観点を明記し、合格判定を数値化。

### 再発防止 memory 化
- 事象を memory 化し、次回 PLAN 起票時に参照可能な learn として保持。

## §4 受入条件 / DoD
- 再現手順が単独で実行できる程度に明確。
- 原因仮説と修正方針が対応し、回帰確認結果が残る。
- 再発防止項目が `memory` 化により追跡可能。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-023
- docs: `helix/HELIX_CORE.md`, `skills/common/documentation/SKILL.md`, `cli/ROLE_MAP.md`
