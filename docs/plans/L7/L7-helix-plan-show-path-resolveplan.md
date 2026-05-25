---
plan_id: L7-helix-plan-show-path-resolveplan
title: "L7-helix-plan-show-path-resolveplan: helix plan show に --path-only と robust plan_id resolution を追加"
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
    - docs/plans/L7/L7-helix-plan-show-subcommandplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — plan show path resolution / path-only 実装"
  - role: qa
    slot_label: "QA — bats / lint / doctor / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-helix-plan-show-path-resolveplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-plan.bats
    artifact_type: bats
---

## §0 PLAN concept

既存 `helix plan show` の frontmatter 表示契約は維持しつつ、解決先 markdown の絶対 path だけを返す `--path-only` を追加する。併せて plan_id/path の解決順序を helper 化し、`docs/plans/**/<plan-id>.md` / `<plan-id>-*.md` / 既存相対 path / 絶対 path を一貫したエラー契約で処理する。

## §1 背景

- `show` は frontmatter 確認用途として有効だが、下流 CLI から「まずファイル位置だけ知りたい」用途に冗長
- 現在の解決ロジックは `cmd_show` 内へ直書きされており、ID 解決順や衝突時エラーが見通しづらい
- `show carry` の延長として path 解決を薄く強化し、既存 `list` / `health` / `lint` / `doctor` を壊さずに利便性だけ上げる

## §2 scope

1. `cli/helix-plan` の `show` に `--path-only` flag を追加する
2. `--path-only` は指定 plan markdown の絶対 path だけを stdout へ 1 行返す
3. `--path-only` と `--json` は排他にする
4. `plan-id-or-path` 解決を helper 化し、path / exact plan file / slug match を堅牢に扱う
5. `cli/tests/test-helix-plan.bats` に `--path-only` の test を 1 件追加する

scope 外:

- `status --frontmatter` や `deps_helper` との共通化
- `helix plan list` / `health` / `lint` / `draft` の契約変更
- `helix doctor` の診断仕様変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 追加 (Red) | `--path-only` の契約が test で固定される | planned |
| .2 | `cli/helix-plan` 実装 | `--path-only` / `--json` 排他 / robust resolve が動作する | planned |
| .3 | 回帰検証 + review | `bash -n` / bats / lint / doctor / settings diff / review が通る | planned |

## §4 受入条件

- `helix plan show <plan-id-or-path> --path-only` が絶対 path を 1 行だけ返す
- `helix plan show --path-only --json` は exit 1 で拒否される
- 既存 `helix plan show` / `show --json` の出力契約は不変
- 既存 15 件の `cli/tests/test-helix-plan.bats` を壊さず、16 件以上 PASS する
- `helix doctor` と `helix plan lint` は既存通り通る

## §5 検証

- `git status --short`
- `bash -n cli/helix-plan`
- `bats cli/tests/test-helix-plan.bats`
- `grep -c 'path-only\\|path_only' cli/helix-plan cli/tests/test-helix-plan.bats`
- `helix plan lint docs/plans/L7/L7-helix-plan-show-path-resolveplan.md`
- `helix doctor`
- `git diff --name-only | grep settings.json`

## §11 carry

- `show` 系 path resolve helper の他 subcommand 共有化は別 PLAN で扱う
