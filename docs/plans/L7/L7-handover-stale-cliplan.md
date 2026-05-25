---
plan_id: L7-handover-stale-cliplan
title: "L7-handover-stale-cliplan: expose handover stale check via CLI subcommand"
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
    - docs/plans/L7/L7-handover-stale-checkplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-handover stale subcommand 実装"
  - role: qa
    slot_label: "QA — bats / bash -n / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-handover-stale-cliplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-handover
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-handover.bats
    artifact_type: test
---

## §0 PLAN concept

W45 で追加済みの `check_handover_staleness()` を shell CLI から直接呼び出せる `helix handover stale` subcommand として公開する。`status` subcommand や Python コアの既存契約は変更せず、thin wrapper と Bats 追加で完結させる。

## §1 背景

- 時間ベース stale 判定は Python helper として実装済みだが、CLI から単独実行できない
- handover の総合 status ではなく、時間ベース freshness だけを軽量確認したい場面がある
- `cli/lib/handover.py` は W45 完了物のため非変更を維持し、shell 側 extension で吸収する

## §2 scope

1. `cli/helix-handover` に `stale` subcommand を追加する
2. `--threshold-hours N` と `--json` を実装する
3. `check_handover_staleness()` を CLI 経由で呼び出す
4. `cli/tests/test-handover.bats` に 2 test を追加する
5. plan lint / bash -n / bats / settings diff で自己検証する

scope 外:

- `cli/lib/handover.py` / `cli/lib/tests/test_handover_stale.py` の変更
- `status` / `dump` / `update` / `clear` / `resume` / `escalate` の挙動変更
- doctor / settings hook の仕様変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + Bats 2 件追加 (Red) | `stale` の no_handover / JSON 契約が test で固定される | planned |
| .2 | `cli/helix-handover` 実装 | `check_handover_staleness()` を direct call し、既存 subcommand 非破壊 | planned |
| .3 | review + bash/bats/plan/settings 検証 | 指定自己検証が全件 PASS | planned |

## §4 受入条件

- `helix handover stale` が no_handover 状態でも exit 0
- `helix handover stale --json` が `status` と `hours_since_update` を含む JSON を返す
- `helix handover stale --threshold-hours N` が helper へ閾値を渡す
- 既存 subcommand の usage / routing を破壊しない
- `bats cli/tests/test-handover.bats` が 39 件以上 PASS

## §11 carry

- `helix handover status` と `stale` の出力整形統一
- doctor からの stale helper 直接利用
