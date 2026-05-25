---
plan_id: L7-test-design-scaffold-function-schemaplan
title: "L7-test-design-scaffold-function-schemaplan: function schema test case scaffold"
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
    - docs/plans/L7/L7-test-design-scaffold-template-extplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — function schema 抽出と skeleton 展開"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint / review 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-function-schemaplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

parent design doc から function 定義を簡易抽出し、test design skeleton の §2 テストケースへ関数別 TC-001..N 雛形を展開する。

## §1 背景

- 現状の scaffold は固定 TC-001 1 件のみで、複数 function を持つ parent design doc の起草支援が弱い
- `L7-test-design-scaffold-template-extplan` で section 引用は実装済みであり、今回はその次段として function schema carry を解消する
- OpenAPI や markdown table の高度解析は scope 外とし、Python def / bash function の簡易抽出に限定する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `extract_function_signatures(paired_design_path: Path, *, max_count: int = 5) -> list[dict[str, str]]` を追加
   - `generate_skeleton(..., extract_functions: bool = False)` を追加
   - `extract_functions=True` のときだけ §2 に TC-001..TC-N を関数別に展開する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 件を追加
   - 既存 14 件の挙動を維持する

scope 外:

- CLI option 追加
- bats 変更
- OpenAPI / markdown table からの endpoint 自動抽出

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | `cli/lib/test_design_scaffold.py` 実装拡張 | pytest 17/17 PASS / py_compile PASS | draft |
| .3 | 検証 + review + plan lint | review 実施 / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `extract_function_signatures()` は Python `def` と bash function を最大 `max_count` 件まで抽出する
- paired design doc 不在時は空 list を返し、例外を出さない
- `generate_skeleton(..., extract_functions=False)` の既定挙動は維持する
- `extract_sections` と `extract_functions` は独立に機能する
- `extract_functions=True` かつ抽出結果ありのとき、§2 に TC-001..TC-N を関数別に展開し、各 TC に function name と signature を blockquote で含める

## §5 検証

- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `grep -c 'extract_function_signatures\\|extract_functions' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-function-schemaplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- API endpoint 自動抽出 (OpenAPI / markdown table 等) は別 PLAN
