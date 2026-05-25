---
plan_id: L7-helix-skill-lint-subcommandplan
title: "L7-helix-skill-lint-subcommandplan: cli/helix-skill に lint subcommand を追加"
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
    - docs/plans/L7/L7-skill-frontmatter-validationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-skill に lint subcommand と human/json 出力を追加"
  - role: qa
    slot_label: "QA — bats 2件、bash -n、plan lint、settings 差分、grep を検証"
generates:
  - artifact_path: docs/plans/L7/L7-helix-skill-lint-subcommandplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-skill
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-skill.bats
    artifact_type: bats
---

## §0 PLAN concept

既存 `cli/lib/skill_frontmatter_lint.py` の `scan_skills_directory()` を `helix skill lint` から呼び出せるようにし、human readable と JSON の両出力を追加する。既存 subcommand と `helix doctor` の挙動は変更しない。

## §1 背景

- W51 で frontmatter lint module は実装済みであり、CLI からの起動経路だけが未提供
- skill root を差し替えて lint を実行できる入口が必要
- 既存 `helix skill` の subcommand 群を壊さず、3 ファイルで変更を閉じる必要がある

## §2 scope

1. `cli/helix-skill` に `lint [--json] [--skills-root PATH]` を追加する
2. default では `total / valid / invalid` と各 error を 1 行ずつ表示する
3. `--json` では `scan_skills_directory()` の結果を JSON で出力する
4. `cli/tests/test-helix-skill.bats` に 2 test を追加する

scope 外:

- `cli/lib/skill_frontmatter_lint.py` の変更
- `cli/lib/tests/test_skill_frontmatter_lint.py` の変更
- `helix doctor` の出力仕様変更
- `.claude/settings.json` / `.vscode/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 2件追加 (Red) | `lint` 実行と `--json` JSON 妥当性が test で固定される | planned |
| .2 | `cli/helix-skill` 実装 | 新 subcommand が default root / custom root / JSON を処理できる | planned |
| .3 | 回帰検証 + self review | `bash -n` / bats / grep / plan lint / settings diff が通る | planned |

## §4 受入条件

- `helix skill lint` は crash せず exit 0 で human readable 集計を返す
- `helix skill lint --json` は `total` / `valid` / `invalid` / `errors` を含む JSON を返す
- `--skills-root PATH` で検査対象 root を差し替えられる
- 既存 `list/show/search/use/chain/classify/review-pending/approve/stats/catalog` を壊さない
- `skill_frontmatter_lint.py` / `test_skill_frontmatter_lint.py` は未変更
- `helix doctor` の既存 frontmatter check を壊さない

## §5 検証

- `git status --short`
- `bash -n cli/helix-skill`
- `bats cli/tests/test-helix-skill.bats`
- `grep -c 'lint)\\|scan_skills_directory' cli/helix-skill`
- `helix plan lint docs/plans/L7/L7-helix-skill-lint-subcommandplan.md`
- `git diff -- .claude/settings.json`

## §11 carry

- warning 表示や exit code policy の細分化は別タスクで扱う
- `helix doctor` と `helix skill lint` の表示統一は別タスクで扱う
