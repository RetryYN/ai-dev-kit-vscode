---
plan_id: L7-test-design-scaffold-interactiveplan
title: "L7-test-design-scaffold-interactiveplan: interactive paired design selection for scaffold CLI"
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
    slot_label: "SE — interactive paired design candidate selection"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff verification"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-interactiveplan.md
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

`auto_detect_paired_design()` に simple stdin ベースの interactive selection を追加し、pair layer 配下の複数 candidate から番号選択できるようにする。未指定時の既定動作は維持し、`--interactive` 明示時だけ prompt を出す。

## §1 背景

- `priority-selection` で status 優先は入ったが、複数の妥当候補から人が選びたい carry が残っている
- TUI は scope 外で、標準入力の 1 回選択だけを実装対象とする
- 既存 49 pytest / 8 bats を壊さず、default は非対話のまま維持する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `list_paired_design_candidates(layer, *, project_root)` を追加
   - `auto_detect_paired_design(..., interactive=False, input_fn=None)` を追加
   - `interactive=True` のとき candidate 一覧を番号付きで表示し、空入力なら sorted 最初を採用する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - candidate list sorted / 番号選択 / 空入力 default の pytest 3 case を追加
3. `cli/helix-test-design-scaffold`
   - 実体は module forwarding のまま利用し、`--interactive` flag を pass-through する
4. `cli/tests/test-helix-test-design-scaffold.bats`
   - `echo '' | ... --interactive` の 1 case を追加

scope 外:

- curses / TUI
- invalid input 再入力ループ
- `generate_skeleton()` / `write_scaffold()` の public API 変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case + bats 1 case 追加 | 追加 test で interactive 仕様が固定される | draft |
| .2 | candidate helper / interactive selection / CLI flag 実装 | py_compile PASS / pytest 52+ PASS | draft |
| .3 | 検証 + review | bats 9+ PASS / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `list_paired_design_candidates()` は sorted な candidate metadata list を返す
- `interactive=True` かつ `input_fn` が `2` を返すと 2 番目候補を採用する
- `interactive=True` かつ空入力なら sorted 最初を default 採用する
- `interactive=False` では既存の auto detect 挙動を維持する
- 既存 pytest 49 件、既存 bats 8 件を破壊しない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -q`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `grep -c 'interactive\\|list_paired_design_candidates' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-interactiveplan.md`
- `git diff --name-only -- .vscode/settings.json .claude/settings.json`

## §11 carry

- invalid input の再入力 UX は将来の TUI / richer prompt 導入時に再検討する
