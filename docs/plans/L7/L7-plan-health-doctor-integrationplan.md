---
plan_id: L7-plan-health-doctor-integrationplan
title: "L7-plan-health-doctor-integrationplan: helix doctor に plan health section を接続"
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
    - docs/plans/L7/L7-plan-health-subcommandplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — doctor に plan health を warn-only 接続"
  - role: qa
    slot_label: "QA — doctor/bats/plan lint/settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-plan-health-doctor-integrationplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: bats
---

## §0 PLAN concept

W61 で追加済みの `scan_all_plans()` を `helix doctor` から読めるようにし、PLAN frontmatter の異常件数を warn-only で日次診断へ露出する。

## §2 scope

1. `cli/helix-doctor` に `[plan health]` section と `check_plan_health` 関数を追加する
2. `scan_all_plans(Path("docs/plans"))` を呼び、invalid 件数だけを概要表示する
3. invalid が 0 件なら pass、1 件以上なら warn とし、doctor 全体は exit 0 を維持する
4. `cli/tests/test-helix-doctor-pmo.bats` に section 出力確認 test を 1 件追加する

scope 外:

- `cli/lib/plan_health.py` と `cli/lib/tests/test_plan_health.py` の変更
- `helix plan health` の出力契約変更
- 既存 doctor section / exit code / strict 挙動の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + Bats 1 件追加 | `[plan health]` section を要求する test が追加される | planned |
| .2 | `cli/helix-doctor` へ warn-only 接続 | `scan_all_plans()` 集計が doctor 出力へ表示される | planned |
| .3 | 回帰検証 + review | `bash -n` / bats / doctor / plan lint / settings diff が通る | planned |

## §4 受入条件

- `helix doctor` 出力に `[plan health]` section が追加される
- section 行は `check plan health: N invalid frontmatter (out of M plans)` を表示する
- invalid 0 件は `✓`、1 件以上は `△` で warn-only を維持する
- `cli/lib/plan_health.py` / `test_plan_health.py` は未変更
- `cli/tests/test-helix-doctor-pmo.bats` 既存 15 件を壊さない

## §5 検証

- `git status --short`
- `bash -n cli/helix-doctor`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `cli/helix doctor`
- `grep -c 'scan_all_plans\\|plan health' cli/helix-doctor`
- `helix plan lint docs/plans/L7/L7-plan-health-doctor-integrationplan.md`
- `git diff -- .claude/settings.json`
