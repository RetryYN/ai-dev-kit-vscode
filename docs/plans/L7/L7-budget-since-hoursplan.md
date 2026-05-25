---
plan_id: L7-budget-since-hoursplan
title: "L7-budget-since-hoursplan: helix-budget status --forecast に --since-hours を追加"
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
    - docs/plans/L7/L7-budget-forecast-cliplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — helix-budget forecast elapsed_hours 可変化"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint / review verification"
generates:
  - artifact_path: docs/plans/L7/L7-budget-since-hoursplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/budget_cli.py
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_budget_cli.py
    artifact_type: test
---

## §0 PLAN concept

既存 `helix budget status --forecast` は `elapsed_hours` を環境変数または 5h block 残時間から推定している。軽量拡張として `--since-hours N` を追加し、forecast の起点を CLI から明示指定できるようにする。未指定時の既定挙動は維持する。

## §1 scope

1. `cli/lib/budget_cli.py`
   - `status` parser に `--since-hours` を追加する
   - `--forecast` 時の `forecast_exhaustion()` に `elapsed_hours=N` を優先注入する
   - `--json` 併用時も同じ forecast を返す
2. `cli/lib/tests/test_budget_cli.py`
   - `--since-hours` が forecast に反映されるテストを追加する
   - `--json --forecast --since-hours` 契約を固定する

scope 外:

- `cli/lib/budget_forecast.py` の API 変更
- 新規サブコマンド追加
- `settings.json` 変更

## §2 設計メモ

- CLI 仕様: `helix budget status --forecast [--since-hours N]`
- `--since-hours` は `float` として受け取り、0 未満は `0.0` に丸める
- `--since-hours` 指定時は `HELIX_BUDGET_WEEKLY_ELAPSED_HOURS` より優先する
- `--since-hours` 未指定時は既存 `_resolve_weekly_elapsed_hours()` をそのまま使う
- `--forecast` 未指定時は `--since-hours` を渡しても表示・JSON は変わらない

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + test 追加 | PLAN 作成 / since-hours 契約を pytest で固定 | draft |
| .2 | `budget_cli.py` 実装 | default 動作不変 / since-hours 伝播 | draft |
| .3 | 検証 + review | py_compile / pytest / grep / plan lint / settings 0 diff | draft |

## §4 受入条件 / DoD

- [ ] `python3 -m py_compile cli/lib/budget_cli.py` が PASS
- [ ] `python3 -m pytest cli/lib/tests/test_budget_cli.py -q` が 11 件以上 PASS
- [ ] `grep -c 'since.hours\\|since_hours' docs/plans/L7/L7-budget-since-hoursplan.md cli/lib/budget_cli.py cli/lib/tests/test_budget_cli.py` が 0 ではない
- [ ] `helix plan lint docs/plans/L7/L7-budget-since-hoursplan.md` が PASS
- [ ] `git diff -- settings.json` が空
- [ ] `helix budget status --forecast` の既定動作が不変

## §5 evidence 方針

- `helix code find "budget forecast since hours"` 実行結果を記録する
- `helix review --uncommitted` を優先し、不可なら理由を残す
- `git status --short` で変更ファイル 3 件を確認する
