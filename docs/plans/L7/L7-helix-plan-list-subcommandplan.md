---
plan_id: L7-helix-plan-list-subcommandplan
title: "L7-helix-plan-list-subcommandplan: helix plan list を docs/plans 一覧へ拡張"
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
    - docs/plans/L7/L7-plan-health-subcommandplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — plan list docs/plans 拡張"
  - role: qa
    slot_label: "QA — bats / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-helix-plan-list-subcommandplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-plan-cmds/list.sh
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-plan.bats
    artifact_type: bats
---

## §0 PLAN concept

既存 `helix plan list` は `.helix/plans/*.yaml` 一覧のみを返す。これを壊さず、`docs/plans/**/*plan.md` frontmatter を主対象に追加し、`--status` / `--kind` / `--layer` / `--json` で一覧取得できるようにする。

## §1 scope

1. `cli/helix-plan-cmds/list.sh` を拡張し、`docs/plans` と `.helix/plans` を横断収集する
2. text 出力は `plan_id + title + status + layer` を 1 行ずつ表示する
3. `--json` は parse 可能な構造化出力を返す
4. 既存 empty state と legacy YAML PLAN 表示は維持する
5. `cli/tests/test-helix-plan.bats` に docs/plans 用の 2 test を追加する

## §2 受入条件

- `helix plan list` が `docs/plans/L7/*.md` の V2 PLAN を一覧表示できる
- `helix plan list --status draft --kind impl --layer L7` が対象 PLAN を絞り込める
- `helix plan list --json` が JSON parse 可能
- `.helix/plans/PLAN-*.yaml` の既存表示を壊さない

## §3 検証

- `git status --short`
- `bash -n cli/helix-plan cli/helix-plan-cmds/list.sh`
- `bats cli/tests/test-helix-plan.bats`
- `grep -c 'list)' cli/helix-plan`
- `helix plan lint docs/plans/L7/L7-helix-plan-list-subcommandplan.md`
- `git diff -- .claude/settings.json`

## §11 carry

- `helix plan --help` の options 詳細表示追加は別タスクでもよい
