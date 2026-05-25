---
plan_id: L7-vmodel-pair-freeze-status-breakdownplan
title: "L7-vmodel-pair-freeze-status-breakdownplan: helix doctor pair freeze status breakdown"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-vmodel-pair-freeze-critical-logic-extplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-strict-modeplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — pair PLAN status breakdown 実装"
  - role: qa
    slot_label: "QA — pytest / bats / doctor / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-status-breakdownplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/vmodel_pair_freeze.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_pair_freeze.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: test
---

## §0 PLAN concept

`helix doctor` の V-model pair freeze section で、pair PLAN の `status` 別件数内訳を表示し、warn-only / strict / active-only の既存契約を壊さずに運用判断材料を増やす。

## §1 背景

- 現状の `check_pair_freeze()` は pair doc の有無だけを返し、どの status の PLAN が存在するかは分からない
- `--vmodel-pair-freeze-active-only` で strict 判定ノイズは減らせるが、通常運用では completed / superseded を含む全体像も欲しい
- doctor 出力に status 別内訳があれば、「missing なのか」「pair PLAN はあるが completed 寄りなのか」を 1 行で判断できる

## §2 scope

1. `check_pair_freeze()` の返却 dict に `status_breakdown` を追加する
2. 内訳対象は `draft / in_progress / completed / superseded / other` とする
3. `status` 不在または未知値は `other` に集約する
4. `cli/helix-doctor` に `status breakdown: ...` 行を追加する
5. `--vmodel-pair-freeze-active-only` 指定時は breakdown 表示を抑止する
6. pytest 3 件、bats 1 件を追加する

scope 外:

- `revised` 日付ベースの期間 filter
- status policy の追加細分化
- severity 契約や strict 判定条件の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件追加 (Red) | PLAN lint PASS / `status_breakdown` 契約が test で固定される | planned |
| .2 | `vmodel_pair_freeze.py` に status breakdown 実装 | 既存 field 維持 + pytest 14 件以上 PASS | planned |
| .3 | `helix-doctor` 表示追加 + bats + 実機確認 | bats 6 件以上 PASS / active-only 既存出力維持 | planned |

## §4 受入条件

- `check_pair_freeze(..., active_only=False)` が既存 field を維持したまま `status_breakdown` を返す
- paired layer では `status_breakdown` に 5 key が揃い、該当 PLAN 数が入る
- `status` 欠損または未知値は `other` へ集計される
- `status=no_pair` の layer では `status_breakdown == {}`
- `helix doctor` 既存の severity 集計表示を維持しつつ、通常モードで breakdown 1 行を追記する
- `helix doctor --vmodel-pair-freeze-active-only` では breakdown を表示しない

## §11 carry

- revised date ベースの期間別 filter は別 PLAN で扱う
