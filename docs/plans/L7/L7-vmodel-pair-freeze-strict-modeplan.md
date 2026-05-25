---
plan_id: L7-vmodel-pair-freeze-strict-modeplan
title: "L7-vmodel-pair-freeze-strict-modeplan: V-model pair freeze strict mode"
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
    - docs/plans/L7/L7-vmodel-pair-freeze-automationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — severity 契約 / strict flag 実装"
  - role: qa
    slot_label: "QA — pytest / bats / doctor 検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-strict-modeplan.md
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

V-model pair freeze の severity 契約を導入し、既定の warn-only を維持したまま `--strict-vmodel-pair-freeze` で critical missing のみ fail-close 化する。

## §1 背景

- tl-advisor W7 助言で「default fail-close は CI 破壊、strict flag または critical-only gate が妥当」と確定
- 既存 `helix doctor` は warn-only で運用されており、既定挙動の破壊は避ける必要がある
- まず severity を返す API と opt-in strict mode を揃え、critical 判定の拡張条件は carry に分離する

## §2 scope

1. `check_pair_freeze()` の返却へ `severity` を追加する
2. `helix doctor --strict-vmodel-pair-freeze` を追加する
3. strict mode では critical missing が 1 件以上のときのみ exit 1 にする
4. pytest 3 件、bats 2 件を追加する

scope 外:

- active PLAN 限定や phase L1-L6 限定などの severity 精密化
- default fail-close 化

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + severity pytest 追加 | PLAN lint PASS / pytest 追加完了 | planned |
| .2 | strict mode bats 追加 + Python 実装 | pytest PASS / doctor default warn-only 維持 | planned |
| .3 | `helix-doctor` strict 判定 + 回帰 | bats PASS / strict PASS/FAIL 両系確認 | planned |

## §4 受入条件

- `cli/lib/vmodel_pair_freeze.py` が `severity: critical|warning|info` を返す
- `helix doctor` の既定動作は exit 0 のまま
- `helix doctor --strict-vmodel-pair-freeze` は critical missing 時のみ exit 1
- 出力に `[V-model pair freeze]` の severity 集計が含まれる

## §11 carry

- critical 判定 logic の拡張（active PLAN 限定 / phase L1-L6 限定など）は別 PLAN で扱う
