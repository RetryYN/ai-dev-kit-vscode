---
plan_id: L7-doctor-summary-jsonplan
title: "L7-doctor-summary-jsonplan: helix doctor --summary 集計 JSON 出力"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires: []
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — doctor summary parser / CLI 接続実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-doctor-summary-jsonplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/lib/doctor_summary.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_doctor_summary.py
    artifact_type: test
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: test
---

## §0 PLAN concept

`helix doctor --summary` を追加し、既存 text 出力を壊さずに `pass_count` / `fail_count` / `warn_count` と section 別 status/count を JSON で返せるようにする。

## §1 scope

1. `cli/helix-doctor` に `--summary` flag を追加する
2. `cli/lib/doctor_summary.py` に `parse_doctor_output(output: str)` を実装する
3. `--summary` は既存 doctor text 出力を parse して JSON を返す
4. `--summary` なしの既存 doctor 動作と exit code を維持する
5. pytest 3 件と bats 1 件で新契約を固定する

scope 外:

- 既存 `--json` schema の変更
- doctor 各 check の内部ロジック変更
- `check_recovery_plan_freshness` サブコマンド拡張

## §2 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + parser pytest 3 件追加 (Red) | PLAN lint PASS / parser 契約固定 | planned |
| .2 | `cli/lib/doctor_summary.py` 実装 + `cli/helix-doctor` 接続 | `helix doctor --summary` が JSON を返す | planned |
| .3 | bats / py_compile / review / settings diff 検証 | pytest 3/3 PASS / bats 13 件以上 PASS / settings 0 diff | planned |

## §3 受入条件

- `helix doctor --summary` は JSON のみを stdout に出力する
- JSON は `pass_count` / `fail_count` / `warn_count` / `sections` を含む
- `sections[]` は `name` / `status` / `count` を持つ
- `parse_doctor_output("")` は全 count 0 / `sections=[]` を返す
- section marker `✓` / `△` / `✗` が `pass` / `warn` / `fail` に対応する
- `helix doctor` デフォルト出力と exit code は不変

## §4 verification

- `bash -n cli/helix-doctor`
- `python3 -m py_compile cli/lib/doctor_summary.py cli/lib/tests/test_doctor_summary.py`
- `python3 -m pytest cli/lib/tests/test_doctor_summary.py -q --tb=short`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `helix plan lint docs/plans/L7/L7-doctor-summary-jsonplan.md`
- `git diff --name-only .claude/settings.json`

## §11 carry

- section count の厳密意味論 (`warnings` / `rows` / advisory 件数のどれを代表値にするか) は CLI 利用実績を見て別 PLAN で refine する
