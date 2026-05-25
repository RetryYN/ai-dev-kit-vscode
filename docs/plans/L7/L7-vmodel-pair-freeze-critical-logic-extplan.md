---
plan_id: L7-vmodel-pair-freeze-critical-logic-extplan
title: "L7-vmodel-pair-freeze-critical-logic-extplan: V-model pair freeze critical 判定 logic 拡張"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-vmodel-pair-freeze-strict-modeplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-automationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — active PLAN filter 実装"
  - role: qa
    slot_label: "QA — pytest / bats / doctor 検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-critical-logic-extplan.md
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

`L7-vmodel-pair-freeze-strict-modeplan` §11 carry-1 の critical 判定 logic 拡張として、active PLAN (`status: draft|in_progress`) のみで pair freeze を集計する option を追加し、strict mode の誤検知を減らす。

## §1 背景

- 現状の critical 判定は pair layer (`L1/L3/L4/L6`) の missing 数のみを見るため、completed / superseded 相当の過去 PLAN まで数えてしまう
- strict mode は opt-in fail-close だが、過去 PLAN 起因の missing が多いと運用ノイズが大きい
- active PLAN 限定 filter を加えると、今まさに進行中の PLAN に対する不足だけを見られる

## §2 scope

1. `check_pair_freeze(layer, *, project_root, active_only=False)` を追加し、active PLAN 限定 filter を提供する
2. 返却 dict に `active_only` field を追加する
3. `helix doctor --vmodel-pair-freeze-active-only` を追加する
4. doctor 出力に `(active-only)` marker を追加する
5. pytest 3 件、bats 1 件を追加する

scope 外:

- completed / superseded / archived など細粒度の status policy 拡張
- critical layer 定義自体の変更
- default fail-close 化

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + active-only pytest 3 件追加 | PLAN lint PASS / pytest fail-first 確認 | planned |
| .2 | `vmodel_pair_freeze.py` に active-only filter 実装 | pytest 11 件 PASS / `active_only` field 返却 | planned |
| .3 | `helix-doctor` flag 追加 + bats + 実機確認 | bats PASS / default warn-only 維持 / active-only marker 出力 | planned |

## §4 受入条件

- `check_pair_freeze(..., active_only=False)` は既存挙動を維持する
- `check_pair_freeze(..., active_only=True)` は `draft|in_progress` の pair PLAN のみカウントする
- 返却 dict に `active_only` field が含まれる
- `helix doctor --vmodel-pair-freeze-active-only` は exit 0 を維持し、strict mode と組み合わせ可能
- `helix doctor --strict-vmodel-pair-freeze --vmodel-pair-freeze-active-only` は active critical missing が 1 件以上のときのみ exit 1

## §11 carry

- status ごとの集計内訳表示や期間別 filter は別 PLAN で扱う
