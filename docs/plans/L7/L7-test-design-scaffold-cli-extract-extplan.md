---
plan_id: L7-test-design-scaffold-cli-extract-extplan
title: "L7-test-design-scaffold-cli-extract-extplan: CLI extract sections flag extension"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-test-design-scaffold-template-extplan.md
    - docs/plans/L7/L7-test-design-scaffoldplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — CLI --extract-sections 接続"
  - role: qa
    slot_label: "QA — bats / syntax / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-cli-extract-extplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-test-design-scaffold.bats
    artifact_type: test
---

## §0 PLAN concept
W13 で実装済みの `generate_skeleton(..., extract_sections=True)` を `helix-test-design-scaffold` CLI から起動可能にする。

## §1 背景
- section 抽出ロジックは実装済みだが、CLI から呼べない
- 本 PLAN では `--extract-sections` を接続し、dry-run / apply の既存導線を保つ

## §2 scope
- `cli/lib/test_design_scaffold.py`: argparse と `write_scaffold(..., extract_sections=...)` 接続
- `cli/tests/test-helix-test-design-scaffold.bats`: `--extract-sections` の acceptance 引用確認を 1 case 追加
- scope 外: unit test 追加変更、parent design 自動検出、wrapper 責務変更

## §3 工程表
| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + bats 1 case 追加 | PLAN 作成 / bats fail で仕様固定 | draft |
| .2 | Python CLI 引数接続 | `--extract-sections` 指定で acceptance 引用が preview に出る | draft |
| .3 | 検証 + review | bats 3/3 PASS / syntax PASS / plan lint PASS / settings 0 diff | draft |

## §4 受入条件
- `helix-test-design-scaffold --extract-sections` が成功し、preview に parent design の受入条件引用を含む
- `--extract-sections` 未指定時は既存 dry-run / apply 挙動を変えない
- 既存 bats 2 件を破壊せず、新規 1 件を追加して合計 3 件以上 PASS する

## §5 検証
- `bash -n cli/helix-test-design-scaffold`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-cli-extract-extplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- `--paired-design` を省略して parent design doc を自動検出するモードは別 PLAN
