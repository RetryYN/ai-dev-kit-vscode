---
plan_id: L7-advance-layer-pair-check-connectplan
title: "L7-advance-layer-pair-check-connectplan: advance_layer 自動 vmodel pair freeze check 連携"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/helix-process/two-stage-agent-design.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-drive-agent-l1-l9-state-extplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-automationplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-strict-modeplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — advance_layer pair freeze warning/timeline 連携"
  - role: qa
    slot_label: "QA — pytest / plan lint / 返却契約回帰確認"
generates:
  - artifact_path: docs/plans/L7/L7-advance-layer-pair-check-connectplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/agent_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_engine.py
    artifact_type: test
---

## §0 PLAN concept

`L7-vmodel-pair-freeze-automationplan` §11 carry-2 を解消し、`AgentEngine.advance_layer()` の `status='entered'` で `check_pair_freeze()` を自動実行する。

- tl-advisor W7 助言に従い、**返却契約は変えない**
- missing pair は **warning / timeline 追加のみ**
- strict 判定や例外化は `C1` と分離し、本 PLAN では扱わない

## §1 背景

- V-model pair freeze API (`check_pair_freeze`) は実装済み
- severity 契約も別 PLAN で整理済み
- 現状は `advance_layer` 実行時に pair freeze 状態が観測されず、carry-2 が未解決

## §2 scope

1. `cli/lib/agent_engine.py`
   - `advance_layer(..., status='entered')` で `check_pair_freeze(layer, project_root=self.project_root)` を呼ぶ
   - `result['status'] == 'pair_missing'` のとき:
     - `session.warnings` に `vmodel pair freeze missing: layer=..., expected_pair=..., severity=...` を追加
     - `session.timeline` に `event='vmodel_pair_warning'` を追加
   - `result['status'] == 'no_pair'` / `ok` は layer 進行を妨げない
2. `cli/lib/tests/test_agent_engine.py`
   - missing / exists / no-pair の 3 ケースを追加
3. PLAN 起票と lint

scope 外:

- `advance_layer` の返却型変更
- `AgentEngineError` への昇格
- `cli/helix-agent` や `helix-doctor` の表示連携
- `cli/lib/vmodel_pair_freeze.py` の API 変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件追加 (Red) | 新規 test が仕様を固定し、既存契約を崩さない | planned |
| .2 | `advance_layer` に warn-only 連携実装 | `advance_layer -> AgentSession` 維持 / 例外化なし | planned |
| .3 | pytest / py_compile / plan lint / grep / settings diff 確認 | 指定自己検証がすべて PASS | planned |

## §4 受入条件

- `advance_layer` の返却型は `AgentSession` のまま
- `status='entered'` でのみ pair freeze check を行う
- `pair_missing` では warning と timeline を追加し、layer 進行は継続する
- `no_pair` / `ok` は warning を増やさない
- `cli/lib/tests/test_agent_engine.py` は既存 21 + 新規 3 で 24 PASS

## §11 carry

- CLI 出力への warning 表示連携は別 carry として扱う
