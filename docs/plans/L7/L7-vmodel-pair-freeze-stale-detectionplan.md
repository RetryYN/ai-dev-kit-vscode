---
plan_id: L7-vmodel-pair-freeze-stale-detectionplan
title: "L7-vmodel-pair-freeze-stale-detectionplan: stale PLAN detection for vmodel pair freeze"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-vmodel-pair-freeze-period-filterplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — stale_count 集計と doctor 表示実装"
  - role: qa
    slot_label: "QA — pytest / bats / doctor / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-stale-detectionplan.md
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

`since_days` filter で集計対象外になった古い pair PLAN を `stale_count` として別集計し、`helix doctor --vmodel-pair-freeze-since-days N` で warning 情報として可視化する。recent 件数の集計契約は維持し、stale 件数は補助情報としてのみ追加する。

## §1 背景

- period filter は最近 updated された pair PLAN だけを集計できるが、期間外に落ちた PLAN 数は分からない
- 運用上は「recent missing」だけでなく、「古い pair PLAN が何件あるか」を同時に見たい
- stale の自動 revised 提案は carry に分離し、今回は count と doctor 表示だけを実装する

## §2 scope

1. `check_pair_freeze()` の返却 dict に `stale_count` を追加する
2. `since_days=None` では `stale_count=0` とする
3. `since_days=N` では N 日より前に revised/created された pair PLAN 件数を `stale_count` に集計する
4. `cli/helix-doctor` の V-model pair freeze section に stale 行を追加する
5. pytest 3 件、bats 1 件を追加する

scope 外:

- stale PLAN の自動 revised 提案
- stale PLAN 一覧の詳細列挙
- strict severity policy の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件 + bats 1 件追加 (Red) | stale_count 契約が test で固定される | planned |
| .2 | `vmodel_pair_freeze.py` に stale_count logic 追加 | 既存 field 維持 + stale_count 返却 | planned |
| .3 | `helix-doctor` stale 表示追加 + 回帰検証 | pytest 20 件以上 PASS / bats 8 件以上 PASS / doctor stale 表示確認 | planned |

## §4 受入条件

- `check_pair_freeze(..., since_days=None)` は既存挙動を維持し、`stale_count == 0`
- `check_pair_freeze(..., since_days=30)` は 30 日以内の pair PLAN だけを recent 判定し、期間外 PLAN を `stale_count` に集計する
- 返却 dict に `stale_count` field が含まれる
- `helix doctor --vmodel-pair-freeze-since-days 30` は既存の severity 行を維持し、`stale (older than 30d): X PLANs` を `stale_count > 0` のときだけ表示する
- 既存 17 pytest / 7 bats の契約を壊さない

## §11 carry

- stale PLAN の自動 revised 提案 (template generator 連携) は別 PLAN で扱う
