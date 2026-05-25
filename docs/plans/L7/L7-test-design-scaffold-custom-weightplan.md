---
plan_id: L7-test-design-scaffold-custom-weightplan
title: "L7-test-design-scaffold-custom-weightplan: custom weight CLI connection"
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
    - docs/plans/L7/L7-test-design-scaffold-priority-weightplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — custom weight 引数の CLI 接続と既定挙動維持"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-custom-weightplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/helix-test-design-scaffold
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
  - artifact_path: cli/tests/test-helix-test-design-scaffold.bats
    artifact_type: bats
---

## §0 PLAN concept

`score_paired_design()` が既に持つ `status_weight` / `kind_weight` を CLI から `--weighted --status-weight N --kind-weight N` で指定できるようにし、既定値 `2 + 1` は変えずに selection policy だけを外出しする。

## §1 背景

- 現状は `weighted=True` を使っても重みは固定で、status/kind の優先度調整を CLI からできない
- W28 では軽量 1 wave で argument path を接続し、既存 29 pytest / 6 bats の互換を維持しながら 2 pytest + 1 bats を追加する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `auto_detect_paired_design(..., status_weight=2, kind_weight=1)` を追加
   - `--weighted` / `--status-weight` / `--kind-weight` を argparse に追加
   - `--weighted` なしで custom weight 指定時は `parser.error` にする
2. `cli/lib/tests/test_test_design_scaffold.py`
   - custom weight 優先 1件、default weight の status 優先 1件を追加
3. `cli/tests/test-helix-test-design-scaffold.bats`
   - `--status-weight` + `--kind-weight` を通す smoke test 1件を追加

scope 外:

- 新しい kind/status 値の追加
- interactive selection UI
- wrapper shell の振る舞い変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 2件 + bats 1件追加 | custom weight と default weight の期待挙動が固定される | draft |
| .2 | argparse / auto-detect 実装 | `weighted=False` 既定挙動を保ったまま custom weight が伝播する | draft |
| .3 | 検証 + review | py_compile / pytest / bats / plan lint / settings diff / review が揃う | draft |

## §4 受入条件

- `helix-test-design-scaffold --layer L4 --weighted --status-weight 3 --kind-weight 2` が成功する
- `auto_detect_paired_design(... weighted=True, status_weight=1, kind_weight=3)` は kind 優先候補を返す
- `auto_detect_paired_design(... weighted=True)` の既定重みは status 優先 (`2 > 1`) を維持する
- `--weighted` なしで `--status-weight` / `--kind-weight` を渡した場合はエラーにする
- 既存 29 pytest / 6 bats と doctor baseline を壊さない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `grep -c 'status_weight\\|kind_weight' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-custom-weightplan.md`
- `git diff --stat .claude/settings.json`
- `helix review --uncommitted`
