---
plan_id: L7-skill-frontmatter-validationplan
title: "L7-skill-frontmatter-validationplan: SKILL.md frontmatter validator を新設"
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
    slot_label: "SE — skill frontmatter lint module と pytest 3件を実装"
  - role: qa
    slot_label: "QA — py_compile / pytest / plan lint / settings 差分を検証"
generates:
  - artifact_path: docs/plans/L7/L7-skill-frontmatter-validationplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/skill_frontmatter_lint.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_skill_frontmatter_lint.py
    artifact_type: test
---

## §0 PLAN concept

`skills/**/SKILL.md` の YAML frontmatter を軽量に検証する専用 module を新設する。今回のスコープは validator 関数と directory scan のみとし、既存 `helix doctor` / `skill_catalog` の実行経路は変更しない。

## §1 背景

- `skill_catalog.py` は frontmatter parse を担うが、field 必須性と品質 warning を独立 API として公開していない
- SKILL.md の frontmatter 品質を後続の doctor 拡張や schema 導入前に単体検証できるようにしたい
- 既存 CLI や settings hook には触れず、新しい area を 3 ファイルで閉じる必要がある

## §2 scope

1. `cli/lib/skill_frontmatter_lint.py` を新規作成する
2. `validate_skill_frontmatter(frontmatter)` を実装し、error / warning findings を返す
3. `scan_skills_directory(skills_root)` を実装し、`skills/**/SKILL.md` の集計結果を返す
4. `cli/lib/tests/test_skill_frontmatter_lint.py` に pytest 3 件を追加する

scope 外:

- `cli/helix-doctor` の call point 追加
- `cli/lib/skill_catalog.py` の既存挙動変更
- `.vscode/settings.json` / `.claude/settings.json` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件追加 (Red) | missing required / short description / aggregate counts が test で固定される | planned |
| .2 | `skill_frontmatter_lint.py` 実装 | validator と directory scan が contract どおりの戻り値を返す | planned |
| .3 | 回帰検証 + self review | py_compile / pytest / plan lint / settings diff が通る | planned |

## §4 受入条件

- `validate_skill_frontmatter()` は `name` / `description` / `triggers` 欠落を `level=error` で返す
- `description` が 50 文字未満のとき `level=warning` を返す
- `skill_id` 欠落は warning として扱う
- `metadata.helix_layer` が指定されている場合、`L1`..`L14` または `all` 以外を error として返す
- `scan_skills_directory()` は `total` / `valid` / `invalid` / `errors` を集計する
- 既存 `helix doctor` / `skill_catalog` / pytest sweep に回帰を入れない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/skill_frontmatter_lint.py cli/lib/tests/test_skill_frontmatter_lint.py`
- `python3 -m pytest cli/lib/tests/test_skill_frontmatter_lint.py -q`
- `grep -c 'validate_skill_frontmatter\\|scan_skills_directory' docs/plans/L7/L7-skill-frontmatter-validationplan.md cli/lib/skill_frontmatter_lint.py cli/lib/tests/test_skill_frontmatter_lint.py`
- `helix plan lint docs/plans/L7/L7-skill-frontmatter-validationplan.md`
- `git diff -- .vscode/settings.json`

## §11 carry

- `helix doctor` への接続は別スプリントで実施する
- 既存 skill 群の `metadata.helix_layer` 互換整理は別タスクで扱う
