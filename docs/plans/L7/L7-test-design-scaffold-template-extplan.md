---
plan_id: L7-test-design-scaffold-template-extplan
title: "L7-test-design-scaffold-template-extplan: test design scaffold template extension"
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
    - docs/plans/L7/L7-test-design-scaffoldplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — parent design section 抽出の実装"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-template-extplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`L7-test-design-scaffoldplan` §11 carry を impl として解消し、test design scaffold template に parent design doc 由来の section 自動抽出を追加する。

- 現状の固定 template (`§0-§3`) は維持する
- `extract_sections=True` のときだけ paired design doc を読み、受入条件 / 機能設計を template に引用する
- CLI 連携や bats 変更は本 PLAN の scope 外とする

## §1 背景

- 現状の `generate_skeleton(layer, paired_design_doc, title)` は固定 template のみを返す
- parent design doc が持つ `受入条件 / DoD / 機能設計 / 関数仕様` を test design 下書きへ再利用できると、起草コストを減らせる
- まずは markdown section の抽出に限定し、高度な schema 解析は別 carry に分離する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `extract_paired_design_sections(paired_design_path: Path) -> dict[str, str]` を追加
   - `generate_skeleton(..., extract_sections: bool = False)` を追加
   - `extract_sections=True` 時のみ `§1 受入条件` と `§2 テストケース` に引用を注入
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 件を追加
   - 既存 5 件の挙動を維持する

scope 外:

- `cli/helix-test-design-scaffold` の option 拡張
- `cli/tests/test-helix-test-design-scaffold.bats` の変更
- parent design doc の関数 schema 解析による test case 自動生成

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | extplan 作成 / pytest fail で仕様固定 | draft |
| .2 | `cli/lib/test_design_scaffold.py` 実装拡張 | pytest 8/8 PASS / py_compile PASS | draft |
| .3 | 検証 + plan lint + settings 差分確認 | plan lint PASS / `.claude/settings.json` 0 差分 | draft |

## §4 受入条件

- `generate_skeleton()` は `extract_sections=False` を default とし、既存挙動を維持する
- `extract_paired_design_sections()` は `受入条件 / 受入要件 / DoD` と `機能設計 / 関数仕様` section を抽出する
- paired design doc が存在しない、または該当 section が無い場合も例外を出さず空 string を返す
- `extract_sections=True` のときだけ extracted section を markdown blockquote 付きで template に反映する
- 既存 pytest 5 件と既存 bats 2 件を破壊しない

## §5 検証

- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `grep -c 'extract_paired_design_sections\\|extract_sections' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-template-extplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- parent design doc の function schema / parameter schema から test case 雛形を生成する高度解析は別 PLAN
