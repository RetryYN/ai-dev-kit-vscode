---
plan_id: L7-budget-forecastplan
title: "L7-budget-forecastplan: helix-budget に exhaustion forecast を追加"
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
  requires: []
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — forecast helper 実装"
  - role: qa
    slot_label: "QA — pytest / py_compile / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-budget-forecastplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/budget_forecast.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_budget_forecast.py
    artifact_type: test
---

## §0 PLAN concept

`helix-budget` の forecast 系ロジックを weekly remaining 観点まで広げるため、消費率から exhaustion date を予測する helper を新規追加する。既存 CLI の公開サブコマンドや既存 `ForecastEngine` の API は壊さず、新 area として独立実装する。

## §1 scope

1. `cli/lib/budget_forecast.py`
   - `forecast_exhaustion()` を新規実装する
   - `current_used_pct` と `elapsed_hours` から消費率、枯渇予測時間、枯渇予測日時、on_track を返す
2. `cli/lib/tests/test_budget_forecast.py`
   - on track / off track / zero elapsed の pytest 3 件を追加する
3. `docs/plans/L7/L7-budget-forecastplan.md`
   - 本 PLAN を起票し、受入条件と検証手順を固定する

scope 外:

- `cli/helix-budget` のサブコマンド追加
- 既存 `status` / `forecast` 出力フォーマット変更
- 既存 pytest sweep の広域見直し

## §2 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 先行追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | `forecast_exhaustion()` 実装 | pytest 3/3 PASS / py_compile PASS | draft |
| .3 | 検証 + review | `helix review --uncommitted` 実施 / plan lint PASS / settings 0 diff | draft |

## §3 API

```python
def forecast_exhaustion(
    *,
    current_used_pct: float,
    elapsed_hours: float,
    period_hours: float = 168,
) -> dict:
    ...
```

返却:

- `projected_exhaustion_hours`: `float | None`
- `projected_exhaustion_date`: ISO 8601 文字列 or `None`
- `rate_per_hour`: `float`
- `on_track`: `bool`

判定仕様:

1. `rate = current_used_pct / elapsed_hours`
2. `remaining_pct = 100 - current_used_pct`
3. `projected_exhaustion_hours = remaining_pct / rate`
4. `projected_exhaustion_date = now + projected_exhaustion_hours`
5. `on_track = projected_exhaustion_hours >= (period_hours - elapsed_hours)`
6. `elapsed_hours == 0` または `rate == 0` の場合は `projected_exhaustion_hours = None`

## §4 受入条件 / DoD

- [ ] `python3 -m pytest cli/lib/tests/test_budget_forecast.py -q` が 3/3 PASS
- [ ] `python3 -m py_compile cli/lib/budget_forecast.py` が PASS
- [ ] `grep -c 'forecast_exhaustion' cli/lib/budget_forecast.py cli/lib/tests/test_budget_forecast.py` が 0 ではない
- [ ] `helix plan lint docs/plans/L7/L7-budget-forecastplan.md` が PASS
- [ ] `settings.json` diff が 0
- [ ] `helix-budget` 既存 API / 既存 pytest sweep を破壊しない

## §5 evidence 方針

- 変更ファイルは 3 件に限定する
- `helix code find "helix-budget"` は実行するが、現環境では recommender session 初期化が read-only file system で失敗しうるため、失敗時は local fallback の結果を evidence に残す
- review 工程は `helix review --uncommitted` を優先し、不可なら理由を残す
