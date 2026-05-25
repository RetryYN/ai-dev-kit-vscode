---
plan_id: L7-test-design-scaffold-auto-detectplan
title: "L7-test-design-scaffold-auto-detectplan: auto-detect paired design plan when CLI flag is omitted"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-test-design-scaffold-cli-extract-extplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-automationplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — auto_detect_paired_design helper と CLI optional flag 化"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-auto-detectplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
  - artifact_path: cli/helix-test-design-scaffold
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-test-design-scaffold.bats
    artifact_type: test
---

## §0 PLAN concept

`helix-test-design-scaffold --layer L4` 実行時に `--paired-design` が省略されたら、V-model pair (`L9`) と `docs/plans/L9/L9-*plan.md` を使って parent design doc を自動検出する。

- `--paired-design` 指定時の既存挙動は維持する
- auto-detect は CLI 層の補助に限定し、`generate_skeleton()` / `write_scaffold()` の public API は変えない
- 複数候補がある場合の選択 UI は carry に分離し、現段階は sorted 最初の 1 件を採用する

## §1 背景

- 現状の `helix-test-design-scaffold` は `--paired-design` 必須のため、軽量な scaffold 起票でも入力が冗長
- `vmodel_pair_freeze.get_pair()` と pair layer 配下の PLAN 配置規約が既にあるため、最小実装で自動補完できる
- template section 抽出は既に CLI 連携済みであり、本 PLAN はその前段の parent design auto-detect だけを追加する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `auto_detect_paired_design(layer: str, *, project_root: Path) -> str | None` を追加
   - `get_pair(layer)` を使い、`docs/plans/L{pair}/L{pair}-*plan.md` の sorted 最初の relative path を返す
   - pair なし、または match なしなら `None`
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 case を追加して helper の仕様を固定する
3. `cli/tests/test-helix-test-design-scaffold.bats`
   - `--paired-design` 省略時の CLI 成功ケースを 1 件追加する
4. `cli/helix-test-design-scaffold` / argparse
   - `--paired-design` を optional にし、省略時は auto-detect
   - 検出失敗時は exit 1 + error を返す

scope 外:

- `generate_skeleton()` / `write_scaffold()` の引数契約変更
- 複数候補があるときの対話的選択 UI
- `helix-doctor` への追加接続

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case + bats 1 case 追加 | PLAN 作成 / 追加 test fail で仕様固定 | draft |
| .2 | `auto_detect_paired_design()` 実装 + CLI optional 化 | pytest 11/11 PASS / py_compile PASS | draft |
| .3 | 検証 + review | bats 4/4 PASS / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `auto_detect_paired_design("L4", project_root=...)` は `docs/plans/L9/L9-*plan.md` の sorted 最初の relative path を返す
- `auto_detect_paired_design("L0", ...)` は pair なしとして `None`
- pair layer directory に match が無い場合は `None`
- CLI で `--paired-design` 指定時は既存挙動維持
- CLI で `--paired-design` 省略時は auto-detect し、見つからなければ exit 1 + error
- 既存 pytest 8 件、既存 bats 3 件を破壊しない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `grep -c 'auto_detect_paired_design' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-auto-detectplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- `docs/plans/L{pair}/` に複数候補がある場合の選択 UI / priority rule は別 PLAN で扱う
