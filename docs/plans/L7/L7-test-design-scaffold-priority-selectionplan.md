---
plan_id: L7-test-design-scaffold-priority-selectionplan
title: "L7-test-design-scaffold-priority-selectionplan: prefer active paired design plan when multiple candidates exist"
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
    - docs/plans/L7/L7-test-design-scaffold-auto-detectplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — prefer_status 優先選択と CLI flag 拡張"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-priority-selectionplan.md
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

`auto_detect_paired_design()` に `prefer_status` を追加し、pair PLAN が複数ある場合は `status: draft` を優先して選ぶ。CLI からは `--prefer-status` で制御し、`none` 指定時だけ従来の sorted 最初へ戻す。

## §1 背景

- 現状は pair layer 配下の sorted 最初を返すため、completed の旧 PLAN が先頭にあると active 候補より優先される
- W20 では selection UI までは入れず、status 優先だけを追加して carry を解消する
- `prefer_kind` や対話的選択 UI は scope 外で、別 PLAN に分離する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `auto_detect_paired_design(layer, *, project_root, prefer_status='draft')` を追加
   - candidate frontmatter の `status` を見て優先選択し、未該当時は sorted 最初へ fallback
   - CLI に `--prefer-status draft|in_progress|completed|none` を追加
2. `cli/lib/tests/test_test_design_scaffold.py`
   - priority 選択、fallback、`None` 無効化の pytest 3 case を追加
3. `cli/tests/test-helix-test-design-scaffold.bats`
   - `--prefer-status` が draft 候補を選ぶことを 1 case 追加

scope 外:

- `prefer_kind` 優先
- 複数候補の対話的 UI
- `generate_skeleton()` / `write_scaffold()` の public API 変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case + bats 1 case 追加 | 追加 test fail で仕様固定 | draft |
| .2 | `prefer_status` 実装 + argparse 拡張 | py_compile PASS / pytest 14+ PASS | draft |
| .3 | 検証 + review | bats 5+ PASS / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `prefer_status='draft'` で draft 候補があれば sorted 順より優先して返す
- 優先 status が無ければ sorted 最初に fallback する
- `prefer_status=None` で既存挙動に戻る
- `--prefer-status none` が `prefer_status=None` に対応する
- 既存 pytest 11 件、既存 bats 4 件を破壊しない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `grep -c 'prefer_status' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-priority-selectionplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- `prefer_kind` 優先や対話的選択 UI は別 PLAN で扱う
