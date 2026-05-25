---
plan_id: L7-helix-plan-show-subcommandplan
title: "L7-helix-plan-show-subcommandplan: helix plan show subcommand 追加"
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
    slot_label: "SE — plan show 実装"
  - role: qa
    slot_label: "QA — bats / lint / doctor / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-helix-plan-show-subcommandplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-plan.bats
    artifact_type: bats
---

## §0 PLAN concept

`helix plan show <plan-id-or-path> [--json]` を追加し、個別 PLAN markdown の frontmatter を軽量に確認できるようにする。`status --frontmatter` は legacy YAML state と混在するため、docs/plans 側の V2 PLAN frontmatter を直接見る専用導線を分離する。

## §1 背景

- `helix plan status --frontmatter` は `--id` 前提で、PLAN markdown を軽く確認したい用途には重い
- V2 PLAN は `L7-*plan` のような frontmatter `plan_id` を持ち、legacy `PLAN-001` と識別子体系が異なる
- `show` は docs/plans frontmatter の単体確認に限定し、既存 `health` / `lint` / `doctor` を壊さずに導線だけ補う

## §2 scope

1. `cli/helix-plan` に `show` subcommand を追加する
2. 引数は `<plan-id-or-path>` 1 つ、`--json` を任意で受ける
3. `plan-id` は `docs/plans/**/<plan-id>.md` と `<plan-id>-*.md` を探索する
4. path 指定時は対象 markdown の frontmatter をそのまま返す
5. 存在しない PLAN は exit 1 + error を返す
6. bats 2 件を追加し、既存 `helix plan` 系テストを不破壊で維持する

scope 外:

- `cli/lib/plan_deps_helper.py` の共通化
- `status --frontmatter` の削除や契約変更
- `helix doctor` / `plan lint` の仕様変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 追加 (Red) | `show` 未実装で追加 bats が失敗する | planned |
| .2 | `cli/helix-plan` に `show` 実装 | `plan-id` / path / `--json` が動作する | planned |
| .3 | 回帰検証 + review | `bash -n` / bats / plan lint / doctor が通る | planned |

## §4 受入条件

- `helix plan show L7-...` で frontmatter を表示できる
- `helix plan show docs/plans/L7/...md` でも同じ frontmatter を表示できる
- `helix plan show --json` は frontmatter mapping を JSON object で返す
- 対象ファイルが存在しない場合は exit 1 + error
- 既存 `helix plan` subcommand と既存 bats を壊さない

## §5 検証

- `git status --short`
- `bash -n cli/helix-plan`
- `bats cli/tests/test-helix-plan.bats`
- `grep -c 'show)' cli/helix-plan`
- `helix plan lint docs/plans/L7/L7-helix-plan-show-subcommandplan.md`
- `helix doctor`
- `git diff -- .vscode/settings.json`

## §11 carry

- `show` / `status --frontmatter` / `deps_helper frontmatter` の実装重複解消は別 PLAN で扱う
