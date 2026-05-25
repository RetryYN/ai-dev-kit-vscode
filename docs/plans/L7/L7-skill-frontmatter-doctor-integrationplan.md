---
plan_id: L7-skill-frontmatter-doctor-integrationplan
title: "L7-skill-frontmatter-doctor-integrationplan: skill_frontmatter_lint を helix-doctor に接続"
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
    - L7-skill-frontmatter-validationplan
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — helix-doctor に skill frontmatter 集計 section を warn-only で接続"
  - role: qa
    slot_label: "QA — bash -n / bats / doctor 出力 / plan lint / settings diff を検証"
generates:
  - artifact_path: docs/plans/L7/L7-skill-frontmatter-doctor-integrationplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: test
---

## §0 PLAN concept

既存の `cli/lib/skill_frontmatter_lint.py` を再利用し、`helix doctor` に skill frontmatter 集計 section を 1 つ追加する。詳細なファイル列挙や verbose 出力には踏み込まず、warn-only の概要表示だけを行う。

## §1 背景

- `L7-skill-frontmatter-validationplan` で validator / scan API は実装済み
- carry として `helix doctor` 配線が残っており、日次の診断導線から見えない
- 今回は doctor section 追加と Bats 1 件追加のみで閉じ、既存 section や exit code 契約を壊さない必要がある

## §2 scope

1. `cli/helix-doctor` に `[skill frontmatter]` section を追加する
2. `scan_skills_directory()` を呼び、invalid 件数だけを集計表示する
3. invalid が 0 件なら pass、0 件超なら warn とし、doctor 全体は exit 0 を維持する
4. `cli/tests/test-helix-doctor-pmo.bats` に section 出力確認 test を 1 件追加する

scope 外:

- `skills/` 配下の実ファイル修正
- `helix skill lint` の詳細表示拡張
- `skill_frontmatter_lint.py` の contract 変更
- `.claude/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + Bats 1 件追加 (Red) | doctor 出力に `[skill frontmatter]` section を要求する test が追加される | planned |
| .2 | `cli/helix-doctor` 配線 | `scan_skills_directory` 呼び出しと warn-only section 出力が実装される | planned |
| .3 | 回帰検証 + self review | `bash -n` / bats / doctor / grep / plan lint / settings diff が通る | planned |

## §4 受入条件

- `helix doctor` 出力に `[skill frontmatter]` section が追加される
- section 行は `check skills/* frontmatter: N invalid skills` 形式で出力される
- invalid 件数 0 の場合は `✓`、1 件以上の場合は `△` で warn-only 表示する
- 既存 doctor section と `cli/tests/test-helix-doctor-pmo.bats` 既存 13 件を壊さない
- `skills/` 配下は read-only scan に留める
- `helix doctor` は新規 fail 化せず exit 0 を維持する

## §5 検証

- `git status --short`
- `bash -n cli/helix-doctor`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `cli/helix doctor`
- `grep -c 'skill_frontmatter_lint\\|scan_skills_directory' cli/helix-doctor`
- `helix plan lint docs/plans/L7/L7-skill-frontmatter-doctor-integrationplan.md`
- `git diff -- .claude/settings.json`

## §11 carry 解消

- `L7-skill-frontmatter-validationplan §11 carry` の doctor integration を本 PLAN で回収する
- 詳細表示や verbose 展開は将来 `helix skill lint` 側の改善タスクで扱う
