---
plan_id: L7-budget-forecast-cliplan
title: "L7-budget-forecast-cliplan: helix-budget status に weekly exhaustion forecast を統合"
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
  requires:
    - docs/plans/L7/L7-budget-forecastplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — helix-budget status forecast 表示統合"
  - role: qa
    slot_label: "QA — pytest / bash -n / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-budget-forecast-cliplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-budget
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_budget_cli.py
    artifact_type: test
---

## §0 PLAN concept

既存 `cli/lib/budget_forecast.py` と `cli/lib/tests/test_budget_forecast.py` で固定済みの exhaustion helper を、`helix budget status` の opt-in 表示へ接続する。デフォルト出力は不変とし、`--forecast` 指定時のみ weekly forecast を 1 行追加する。

## §1 scope

1. `cli/helix-budget`
   - `status [--forecast]` を help に追記する
2. `cli/lib/budget_cli.py`
   - `status --forecast` を parser に追加する
   - Claude weekly used % と elapsed hours から `forecast_exhaustion()` を呼ぶ
   - 非 `--forecast` では既存出力を維持する
3. `cli/lib/tests/test_budget_cli.py`
   - `status --forecast` の dispatch と stdout 契約を追加する

scope 外:

- 新規サブコマンド追加
- `cli/lib/budget_forecast.py` の API 変更
- `settings.json` 変更

## §2 設計メモ

- 表示は `forecast (weekly): projected exhaustion in 24h (off track)` 形式
- `elapsed_hours` は次の優先順で解決:
  1. `HELIX_BUDGET_WEEKLY_ELAPSED_HOURS`
  2. `ccusage blocks` 由来の active 5h block 残り時間から推定
  3. fallback `0`
- `elapsed_hours == 0` の場合は `forecast (weekly): unavailable (elapsed 0h)` を表示
- `--forecast` は opt-in。既存 `status` の default 動作は不変

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + CLI test 追加 | PLAN 作成 / forecast 契約を pytest で固定 | draft |
| .2 | `status --forecast` 実装 | 既存 status 不破壊 / pytest PASS | draft |
| .3 | 検証 + review | `bash -n` / pytest / plan lint / settings 0 diff | draft |

## §4 受入条件 / DoD

- [ ] `python3 -m pytest cli/lib/tests/test_budget*.py -q` が全 PASS
- [ ] `bash -n cli/helix-budget` が PASS
- [ ] `grep -c 'forecast' cli/helix-budget cli/lib/tests/test_budget_cli.py` が 0 ではない
- [ ] `helix plan lint docs/plans/L7/L7-budget-forecast-cliplan.md` が PASS
- [ ] `settings.json` diff が 0
- [ ] `helix budget status` の default 出力が不変

## §5 evidence 方針

- `helix code find "budget forecast"` を実行し、失敗時は local fallback 制約を evidence に残す
- `helix review --uncommitted` を優先し、不可なら理由を残す
- `git status --short` で変更ファイル 3-4 件を確認する
