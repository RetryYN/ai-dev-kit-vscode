---
plan_id: L7-auto-run-loop-frameworkplan
title: "L7-auto-run-loop-frameworkplan: 指定時間・heartbeat・compaction 連携を統合する自動走行ループ roadmap"
kind: design
layer: L7
drive: be
status: draft
process_layer: L7
parent_design: HELIX-workflows/helix-process/continuous-run-context-management.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/integration-map.md
    - HELIX-workflows/helix-process/continuous-run-context-management.md
    - HELIX-workflows/HELIX-process-L0-L14.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — framework 架構の定義と hook 方針の整備"
  - role: pmo-sonnet
    slot_label: "PMO — DoD と受入条件の記録"
generates:
  - artifact_path: docs/plans/L7/L7-auto-run-loop-frameworkplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-auto-run
    artifact_type: markdown_doc
---

## §0 PLAN concept

指定時間起動・budget time window・heartbeat wake・PLAN 再開・compaction API を軸に、自動走行ループの road map を設計のみで起票する。

対象:
- SoT: `HELIX-workflows/helix-process/continuous-run-context-management.md`
- 目的: BE 文脈で `continuous-run` を実装前提で統合する設計基盤を用意する
- スコープ: PLAN 起票のみ（実装は別 session）

## §1 背景

- コンテキスト駆動実行が継続的に再開されるためには、時間窓・heartbeat・PLAN 再開・compaction が契約として先に固定される必要がある。
- 継続実行ループの仕様が個別文書化される一方、helix plan / doctor で追跡しやすい roadmap 化が未着手。
- 本 PLAN は設計起点（framework）として、将来実装の最短経路を固定する。

## §2 scope

1. `L7-auto-run-loop-frameworkplan` を roadmap として新規作成。
2. 対象コンポーネントを `cli/helix-auto-run`（将来）と hook 連携対象に明示。
3. 4 mode 運用を阻害しない時間管理・復元設計（budget window / wake / resume）を `scope` として分解。
4. `integration-map.md` 該当行へ PLAN-roadmap-起票注記を追記。

scope 外:
- 実行基盤（daemon / CI runner / スケジューラ）の実装
- compaction API 本体実装

## §3 工程表 (placeholder)

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | 連続走行の SoT と責務分解 | 利害関係範囲が明文化される | planned |
| .2 | `continuous-run-context-management` との対照表を作成 | plan lint と frontmatter parse 条件を満たす | planned |
| .3 | 実装移行向け acceptance 条件を記録 | 実装 session へ引き継げる状態 | planned |

## §11 carry

- carry-1: 指定時間/heartbeat/compaction の文脈を単一 PLAN に統合
- carry-2: 自動走行フック設計（起動・再開・停止）を blueprint 化
- carry-3: 実装可否判断は次実装 session に委譲

