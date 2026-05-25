---
plan_id: L7-plan-lint-cli-validateplan
title: "L7-plan-lint-cli-validateplan: helix plan lint に --validate-frontmatter / --json を追加"
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
  requires:
    - docs/plans/L7/L7-plan-lint-frontmatter-validationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — lint CLI flag / JSON 実装"
  - role: qa
    slot_label: "QA — bats / lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-plan-lint-cli-validateplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/plan_lint.py
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-plan-lint.bats
    artifact_type: bats
---

## §0 目的

W49 で追加済みの `validate_plan_frontmatter` を `helix plan lint` から明示的に呼べるようにし、同結果を `--json` で機械可読化する。

## §1 scope

- `helix plan lint --validate-frontmatter <plan-file>`
- `helix plan lint --validate-frontmatter --json <plan-file>`
- 既存の status lint / duplicate lint / legacy skip は不破壊
- Bats に 1-2 case 追加

## §2 実装方針

1. `cli/lib/plan_lint.py` に `--validate-frontmatter` / `--json` を追加する
2. JSON 出力は frontmatter / status_lint / duplicates を分離して返す
3. `cli/helix-plan-cmds/lint.sh` で新規 flag を透過させる
4. `cli/tests/test-helix-plan-lint.bats` に valid PLAN と JSON parse の 2 test を追加する

## §3 受入条件

- valid な V2 PLAN へ `helix plan lint --validate-frontmatter` を実行すると exit 0
- `--validate-frontmatter --json` は parse 可能で、`frontmatter.validated == true` を含む
- 既存の 17 test を壊さない
- `helix doctor` 既存挙動を変えない

## §4 検証

- `bash -n cli/helix-plan cli/helix-plan-cmds/lint.sh`
- `python3 -m py_compile cli/lib/plan_lint.py`
- `bats cli/tests/test-helix-plan-lint.bats`
- `grep -c 'validate_plan_frontmatter\\|validate-frontmatter' docs/plans/L7/L7-plan-lint-cli-validateplan.md cli/lib/plan_lint.py cli/tests/test-helix-plan-lint.bats`
- `./cli/helix plan lint --validate-frontmatter docs/plans/L7/L7-plan-lint-cli-validateplan.md`
- `./cli/helix plan lint --validate-frontmatter --json docs/plans/L7/L7-plan-lint-cli-validateplan.md`
- `git diff -- .vscode/settings.json`
