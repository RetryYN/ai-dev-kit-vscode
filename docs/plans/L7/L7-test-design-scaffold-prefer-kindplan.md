---
plan_id: L7-test-design-scaffold-prefer-kindplan
title: "L7-test-design-scaffold-prefer-kindplan: prefer kind-filtered paired design plan candidates"
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
    - docs/plans/L7/L7-test-design-scaffold-priority-selectionplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — auto_detect_paired_design prefer_kind + CLI flag 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-prefer-kindplan.md
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

`auto_detect_paired_design()` に `prefer_kind` を追加し、CLI `--prefer-kind` から `design|impl|poc|none` を渡せるようにする。候補が複数あるときは `status + kind` の両一致を最優先し、未該当時は段階的に fallback する。

## §1 背景

- 既存実装は `prefer_status` のみを見ており、同 status 内で `design` / `impl` / `poc` の優先選択ができない
- W22 では `prefer_kind` の追加までを scope とし、複合 priority UI や rank table は carry のまま残す

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `auto_detect_paired_design(..., prefer_kind=None)` を追加
   - fallback chain: `status+kind` → `status` → `kind` → sorted 最初
   - CLI `--prefer-kind design|impl|poc|none` を追加
2. `cli/lib/tests/test_test_design_scaffold.py`
   - kind 優先、kind fallback、status+kind 組合せの pytest 3 case を追加
3. `cli/tests/test-helix-test-design-scaffold.bats`
   - `--prefer-kind` の bats 1 case を追加

scope 外:

- status と kind の重み付け UI
- `generate_skeleton()` / `write_scaffold()` の API 変更
- pair 候補の対話選択

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest/bats 追加 | 追加 test fail で仕様固定 | draft |
| .2 | `prefer_kind` 実装 + CLI 拡張 | py_compile PASS / pytest 20 PASS | draft |
| .3 | 検証 + review | bats 6 PASS / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `prefer_kind='design'` で design 候補があれば優先して返す
- `prefer_status='draft'` と `prefer_kind='design'` を同時指定した場合、両一致候補を最優先する
- `prefer_kind` 未該当時は既存の status 優先または sorted fallback を維持する
- `--prefer-kind none` は filter 無効化として扱う
- 既存 pytest 17 件、既存 bats 5 件を破壊しない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `grep -c 'prefer_kind' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-prefer-kindplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- `prefer_status` と `prefer_kind` の重み付け優先順位表は別 PLAN で扱う
