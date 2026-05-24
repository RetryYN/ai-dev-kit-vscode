---
plan_id: L7-auto-run-loop-frameworkplan
title: "L7-auto-run-loop-frameworkplan: 指定時間・heartbeat・compaction 連携を統合する自動走行ループ roadmap"
kind: design
layer: L7
drive: be
status: completed
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

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | 連続走行の SoT と責務分解 | 利害関係範囲が明文化される | completed |
| .2 | `cli/helix-auto-run` skeleton + `cli/lib/auto_run_engine.py` 実装 | start / status / resume / stop / heartbeat / budget が最小動作する | completed |
| .3 | pytest / bats / docs / router / PLAN status 更新 | minimal viable foundation が検証付きで残る | completed |

## §11 carry

- carry-1: compaction API 統合は next phase。現時点では `integrations.compaction_api = pending_next_phase` の接続点のみ保持
- carry-2: ScheduleWakeup / hook 統合は scope 外。heartbeat 判定は `cli/helix-heartbeat-scheduler` 呼び出しまで
- carry-3: full autonomous loop の本格検証・長時間連続稼働確認は次 PLAN へ持ち越し
