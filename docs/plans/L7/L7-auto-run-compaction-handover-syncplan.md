---
plan_id: L7-auto-run-compaction-handover-syncplan
title: "L7-auto-run-compaction-handover-syncplan: compaction 後の handover state 整合"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_design: HELIX-workflows/helix-process/continuous-run-context-management.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-auto-run-poc-compaction-apiplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — handover snapshot helper 実装"
  - role: qa
    slot_label: "QA — pytest / py_compile / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-auto-run-compaction-handover-syncplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/compaction_adapter.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_compaction_adapter.py
    artifact_type: test
---

## §0 PLAN concept

`L7-auto-run-poc-compaction-apiplan` §11 carry-3 を閉じるため、compaction 実行直後に `.helix/handover/CURRENT.json` の snapshot を収集し、dry-run/監査保存の両モードで再利用できる helper を追加する。

## §1 背景

- compaction PoC は drift 判定と state 保存まで実装済みだが、handover 状態との整合 snapshot は未実装。
- `continuous-run-context-management` は handover 記録が継続実行の再開条件であることを前提にしている。
- compaction 後の handover snapshot を同じ helper で返すことで、後続 wave の監査と resume 判定に流用しやすくする。

## §2 scope

1. `cli/lib/compaction_adapter.py` に `sync_handover_after_compaction()` を追加する。
2. compaction 直後に `project_root/.helix/handover/CURRENT.json` を読み、`exists / updated_at / next_action_summary` の snapshot を返す。
3. `dry_run=False` のときは `.helix/handover/COMPACTION-SYNC.json` に監査用 snapshot を保存する。
4. `cli/lib/tests/test_compaction_adapter.py` に 3 test を追加し、既存 5 test を不破壊で維持する。

scope 外:
- handover schema 自体の変更
- compaction API の実呼び出し
- auto_run_engine への追加配線

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + 既存 compaction/handover shape 確認 | frontmatter と依存が lint 可能 | completed |
| .2 | handover sync helper の TDD 実装 | dry_run / synced / no_handover の 3 分岐が pytest で固定化される | completed |
| .3 | review / py_compile / pytest / plan lint / settings diff 確認 | pytest 8/8 PASS、settings 0 diff、plan lint PASS | completed |

## §4 実装方針

- `request_compaction()` の既存返却型は変更しない。
- handover snapshot は read-only 要約に限定し、`next_action_summary` は 200 文字で切り詰める。
- 監査ファイルは `COMPACTION-SYNC.json` とし、書き込みは helper 呼び出し時のみ行う。

## §5 検証

- `python3 -m pytest cli/lib/tests/test_compaction_adapter.py -v`
- `python3 -m py_compile cli/lib/compaction_adapter.py`
- `helix review --uncommitted`
- `helix plan lint docs/plans/L7/L7-auto-run-compaction-handover-syncplan.md`

## §11 carry

- carry-1: 後続 wave で `auto_run_engine` から本 helper を呼び出す配線
