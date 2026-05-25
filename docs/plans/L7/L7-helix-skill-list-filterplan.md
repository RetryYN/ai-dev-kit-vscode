---
plan_id: L7-helix-skill-list-filterplan
title: "L7-helix-skill-list-filterplan: cli/helix-skill list の filter 拡張"
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
    - docs/plans/L7/L7-helix-skill-show-subcommandplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-skill list の layer/category filter を複数値対応へ拡張"
  - role: qa
    slot_label: "QA — bats 2件、bash -n、plan lint、settings 差分を検証"
generates:
  - artifact_path: docs/plans/L7/L7-helix-skill-list-filterplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-skill
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-skill.bats
    artifact_type: bats
---

## §0 PLAN concept

`helix skill list` には既に `--layer` / `--category` が存在するため、単純追加ではなくカンマ区切り複数値 filter へ拡張する。既存の単一値 filter と `--json` は後方互換で維持する。

## §1 背景

- TASK_INPUT の前提確認により `list` には既存 filter が実装済みだった
- 既存の単一値 filter は軽量だが、複数 layer / category を横断した確認で再実行が必要になる
- 変更は 3 ファイルに閉じ、既存 `helix skill` subcommand と Bats を壊さずに拡張する必要がある

## §2 scope

1. `cli/helix-skill` の `list` を `--layer L2,L7` / `--category common,workflow` 形式に対応させる
2. 単一値 filter と `--json` 出力の後方互換を維持する
3. `cli/tests/test-helix-skill.bats` に複数値 filter を固定する test を 2 件追加する

scope 外:

- `search` / `chain` の filter 振る舞い変更
- `cli/lib/skill_recommender.py` の変更
- `helix doctor` の仕様変更
- `.claude/settings.json` / `.vscode/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 2件追加 (Red) | 複数値 filter 契約が test で固定される | planned |
| .2 | `cli/helix-skill` 実装 | `list` が `--layer/--category` のカンマ区切り複数値を受け付ける | planned |
| .3 | 回帰検証 + self review | `bash -n` / bats / grep / plan lint / settings diff が通る | planned |

## §4 受入条件

- `helix skill list --layer L2,L7` で両方の layer に属する skill だけを表示できる
- `helix skill list --category common,workflow` で両方の category に属する skill だけを表示できる
- 既存の単一値 `--layer` / `--category` はそのまま動作する
- `--json` 出力は filter 後の `skills` / `skill_count` を正しく返す
- 既存 `show/lint/catalog/classify/search/use/chain/stats/review-pending/approve/audit-layers` を壊さない

## §5 検証

- `git status --short`
- `bash -n cli/helix-skill`
- `bats cli/tests/test-helix-skill.bats`
- `grep -c 'layer\\|category' cli/helix-skill`
- `helix plan lint docs/plans/L7/L7-helix-skill-list-filterplan.md`
- `git diff -- .claude/settings.json .vscode/settings.json`

## §11 carry

- `search` / `chain` 側にも複数値 filter を合わせるかは別タスクで扱う
- invalid filter 値の strict mode 導入は別タスクで扱う
