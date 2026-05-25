---
plan_id: L7-helix-skill-show-subcommandplan
title: "L7-helix-skill-show-subcommandplan: cli/helix-skill に show subcommand を追加"
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
    - docs/plans/L7/L7-helix-skill-lint-subcommandplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-skill の show を frontmatter 表示へ拡張"
  - role: qa
    slot_label: "QA — bats 2件、bash -n、plan lint、settings 差分を検証"
generates:
  - artifact_path: docs/plans/L7/L7-helix-skill-show-subcommandplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-skill
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-skill.bats
    artifact_type: bats
---

## §0 PLAN concept

`helix skill show <skill-id> [--json]` を追加し、個別 `SKILL.md` の YAML frontmatter を軽量に確認できるようにする。既存 catalog 詳細表示より軽い導線に切り替え、`--with-content` は後方互換のため残す。

## §1 背景

- `helix skill` には `show` help があるが、frontmatter を直接見る用途には重い
- skill frontmatter lint / audit の前提として、単一 skill の frontmatter を軽く確認したい
- 変更は 3 ファイルに閉じ、既存 subcommand と bats を壊さずに拡張する必要がある

## §2 scope

1. `cli/helix-skill` の `show` を `SKILL.md` frontmatter 直接表示に切り替える
2. `--json` で frontmatter を JSON object として返す
3. 存在しない skill は exit 1 + error を返す
4. `cli/tests/test-helix-skill.bats` に 2 test を追加する

scope 外:

- `cli/lib/skill_catalog.py` の変更
- `cli/lib/skill_frontmatter_lint.py` の変更
- `helix doctor` の仕様変更
- `.claude/settings.json` / `.vscode/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 2件追加 (Red) | `show` の frontmatter / JSON 契約が test で固定される | planned |
| .2 | `cli/helix-skill` 実装 | `show <skill-id> [--json]` が frontmatter を返す | planned |
| .3 | 回帰検証 + self review | `bash -n` / bats / grep / plan lint / settings diff が通る | planned |

## §4 受入条件

- `helix skill show <existing-skill>` で `SKILL.md` frontmatter を表示できる
- `helix skill show <existing-skill> --json` で frontmatter の JSON object を返す
- 存在しない skill は exit 1 + error を返す
- 既存 `list/lint/catalog/classify/search/use/chain/stats/review-pending/approve/audit-layers` を壊さない
- `--with-content` は後方互換のため維持する

## §5 検証

- `git status --short`
- `bash -n cli/helix-skill`
- `bats cli/tests/test-helix-skill.bats`
- `grep -c 'show)' cli/helix-skill`
- `helix plan lint docs/plans/L7/L7-helix-skill-show-subcommandplan.md`
- `git diff -- .claude/settings.json .vscode/settings.json`

## §11 carry

- `show` / `lint` / `audit-layers` の frontmatter 共通 helper 化は別タスクで扱う
- bare skill name の曖昧解決ポリシー強化は別タスクで扱う
