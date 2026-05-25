---
plan_id: L7-budget-json-outputplan
title: "L7-budget-json-outputplan: helix-budget status --json に summary と per-source breakdown を追加"
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
    slot_label: "SE — budget JSON summary / per-source breakdown 実装"
  - role: qa
    slot_label: "QA — pytest / bash -n / review / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-budget-json-outputplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/budget_cli.py
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_budget_cli.py
    artifact_type: test
---

## §0 PLAN concept

`helix budget status --json` は既存の raw status を返しているが、CLI 契約としては source 別の使用率要約が弱い。既存フィールドは保持したまま、`summary` と `per_source_breakdown` を追加し、`--forecast` 併用時は top-level `forecast` も返す。

## §1 scope

1. `cli/lib/budget_cli.py`
   - `status --json` 用の整形 helper を追加する
   - 既存 raw status を壊さず `summary` / `per_source_breakdown` / `forecast` を追加する
2. `cli/lib/tests/test_budget_cli.py`
   - JSON 出力契約を固定する pytest を 2 件追加する

scope 外:

- `collect_status()` の返却 schema 変更
- `cli/helix-budget` help 文面の構造変更
- `settings.json` 変更

## §2 JSON 契約

- `summary.claude|codex` は `source` / `used_pct` / `remaining` を持つ
- `per_source_breakdown` は少なくとも `claude_weekly` / `codex_five_hour` / `codex_weekly` を持つ
- `claude_block` は block 情報がある場合のみ追加する
- `--forecast` 指定時は top-level `forecast` を追加し、raw `claude.weekly_forecast` も維持する
- 非 `--json` 出力と default 動作は不変

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + JSON pytest 追加 | PLAN 作成 / JSON 契約を Red で固定 | draft |
| .2 | `budget_cli.py` 実装 | `summary` / `per_source_breakdown` / `forecast` が JSON に載る | draft |
| .3 | 検証 + review | `bash -n` / `py_compile` / pytest / plan lint / settings 0 diff | draft |

## §4 verification

- `bash -n cli/helix-budget`
- `python3 -m py_compile cli/lib/budget_cli.py cli/lib/tests/test_budget_cli.py`
- `python3 -m pytest cli/lib/tests/test_budget_cli.py -q --tb=short`
- `grep -c 'json' cli/lib/budget_cli.py`
- `helix plan lint docs/plans/L7/L7-budget-json-outputplan.md`
- `git diff --name-only .claude/settings.json`

## §11 evidence

- `helix code find "budget"` は local fallback 経由で失敗しているため、その旨を evidence に残す
- `helix review --uncommitted` を優先する
- `git status --short` で変更ファイルが 3 件であることを確認する
