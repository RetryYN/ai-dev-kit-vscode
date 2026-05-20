---
plan_id: PLAN-NNN-poc-slug
title: "PLAN-NNN: (PoC タイトル placeholder)"
kind: poc
layer: cross
drive: scrum
workflow_phase: S2
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: se
    slot_label: "SE — PoC 実装"
  - role: qa
    slot_label: "QA — verify スクリプト実行・結果確認"
generates:
  - artifact_path: verify/<poc-name>.sh
    artifact_type: script
  - artifact_path: cli/lib/tests/test_<poc-module>.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-NNN-poc-result.md
    artifact_type: doc_update
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
PLAN-091 の PoC kind 実行を標準化し、S0〜S4 を順番どおり記録する。

## §1 目的
実現可能性・リスク・検証条件を短いサイクルで確定し、Forward 接続可否を明文化する。

## §2 背景
- PoC の段階で検証項目が散在し、verify 手順の再実行可能性が低い。
- PLAN-091 では `verify/*.sh` 全件実行の実績を固定的に残す必要がある。

## §3 実装計画
### S0: Backlog 構築
- 実験仮説、制約、検証前提条件、評価軸を 1 枚にまとめる。

### S1: Sprint Plan
- 各検証項目を Sprint unit に落とし、成功条件（DoD）を明記した実行順を定義。

### S2: PoC 実装
- 最小実装（または既存実装の有効切替）で検証条件を満たす経路を作成。

### S3: Verify（全 verify/*.sh 実行）
- `verify/` 配下の `*.sh` を網羅実行し、成功/失敗と差分、再実行方法を記録。

### S4: Decide
- 判定は `confirmed / rejected / pivot` の 3 件に限定し、選択理由と再開条件を記載。

## §4 受入条件 / DoD
- S0〜S4 を省略なく記載。
- S3 で全 verify 実行ログが残され、再現手順が明示。
- 判定が `confirmed / rejected / pivot` のいずれかに確定。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-021（調査ガード）, ADR-024（実行ハンドリング）
- docs: `docs/commands/ai-harness.md`, `helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`
