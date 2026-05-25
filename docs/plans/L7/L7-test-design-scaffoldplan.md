---
plan_id: L7-test-design-scaffoldplan
title: "L7-test-design-scaffoldplan: test design doc dry-run scaffold"
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
    - docs/plans/L7/L7-vmodel-pair-freeze-automationplan.md
    - docs/plans/L7/L7-vmodel-pair-freeze-strict-modeplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — test design scaffold 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffoldplan.md
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

`L7-vmodel-pair-freeze-automationplan` §11 carry-3 の test design doc skeleton 自動展開を、tl-advisor 助言どおり「明示 command + dry-run default」で実装する。

- doctor は検出のみを維持し、自動生成トリガには接続しない
- 低品質な量産を避けるため、既定は dry-run、実書き込みは `--apply` 明示時のみ

## §1 背景

- V-model pair freeze で 11 件の missing pair docs が検出済み
- 手動で test design doc を起票すると時間がかかり、pair freeze の解消が滞る
- 一方で自動書き込みを既定にすると、未精査の skeleton が量産されやすい
- dry-run scaffold を先に出し、利用者が確認して `--apply` する導線に限定する

## §2 scope

1. `cli/lib/test_design_scaffold.py` を新規追加する
   - `generate_skeleton(layer, paired_design_doc, *, title=None)` を実装
   - `write_scaffold(..., dry_run=True, output_path=None)` を実装
   - pair layer 解決、title 推定、auto output path 生成を行う
2. `cli/helix-test-design-scaffold` を新規追加する
   - default dry-run
   - `--apply` 時のみ実書き込み
   - `status / output_path / content_preview` を出力する
3. `cli/lib/tests/test_test_design_scaffold.py` と `cli/tests/test-helix-test-design-scaffold.bats` を新規追加する
   - pytest 5 case
   - bats 2 case

scope 外:

- `helix-doctor` への自動接続
- `agent_engine.advance_layer()` からの自動起動
- parent design doc からの高度な section 自動抽出
- 既存 `helix-doctor` / `vmodel_pair_freeze.py` / `agent_engine.py` の変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 5 case 追加 | PLAN 作成 / pytest fail で仕様固定 | completed |
| .2 | `cli/lib/test_design_scaffold.py` 実装 | pytest 5/5 PASS / py_compile PASS | completed |
| .3 | CLI wrapper + bats 2 case 追加 | bats 2/2 PASS / plan lint PASS | completed |

## §4 受入条件

- `generate_skeleton()` が pair layer・paired design path・§0-§3 の template を含む
- `write_scaffold()` は `dry_run` / `applied` / `skipped` を返す
- default は dry-run で、書き込みは `--apply` 明示時のみ
- 既存 path には上書きせず `status='skipped'` を返す
- CLI は `status / output_path / content_preview (先頭 20 行)` を stdout 出力する

## §5 検証

- python3 -m py_compile cli/lib/test_design_scaffold.py: PASS
- python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v: 5/5 PASS
- bats cli/tests/test-helix-test-design-scaffold.bats: 2/2 PASS
- bash -n cli/helix-test-design-scaffold: PASS
- helix plan lint docs/plans/L7/L7-test-design-scaffoldplan.md: PASS
- git diff --stat .claude/settings.json: 0 差分

## §11 carry

- parent design doc 構造からの section 自動抽出は別 PLAN で扱う
