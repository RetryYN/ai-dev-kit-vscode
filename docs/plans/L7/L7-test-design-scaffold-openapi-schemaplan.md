---
plan_id: L7-test-design-scaffold-openapi-schemaplan
title: "L7-test-design-scaffold-openapi-schemaplan: OpenAPI parameter schema detail extraction"
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
    - docs/plans/L7/L7-test-design-scaffold-openapi-detailplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — OpenAPI parameter schema detail extraction and scaffold rendering"
  - role: qa
    slot_label: "QA — pytest / py_compile / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-openapi-schemaplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`extract_openapi_endpoints()` の `parameters` entry を name-only list から schema detail 付き list へ拡張し、`generate_skeleton()` 側で `name (type, required|optional)` 表示にする。

## §1 背景

- 現状は parameter name しか抽出せず、TC 起草時に type / required / example を手動補完している
- W31 では component schema 解決までは踏み込まず、parameter object 自体の detail だけを扱う
- downstream 表示は legacy `str` entry も許容し、既存 wave の互換性を維持する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - OpenAPI parameter を `{'name', 'in', 'type', 'required', 'example'}` 形式で抽出する
   - schema / example 不在時は default 値を設定する
   - skeleton 表示は dict と str の両形式を許容する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 件を追加し、詳細抽出・default 値・backward compatibility を固定する
   - 既存 parameter assertion は name 部分のみを確認する形へ調整する

scope 外:

- `$ref` / component schemas 解決
- responses / request body detail の追加拡張
- CLI option 追加

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | parameter schema detail 実装 | pytest 37/37 PASS / py_compile PASS | draft |
| .3 | 検証 + review + lint | review 実施 / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- OpenAPI parameter は `name`, `in`, `type`, `required`, `example` を持つ dict として抽出される
- `schema.type` 不在時は `unknown`、`example` 不在時は空文字、`required` 不在時は `False` を使う
- `generate_skeleton()` は dict entry を `name (type, required|optional)`、str entry を name のみで表示する
- 既存の name-only 利用者は str/dict 判定で互換利用できる
- 既存 34 pytest を壊さず、追加 3 件を含め 37/37 PASS とする

## §5 検証

- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `grep -c "type.*required\\|parameter_schema" cli/lib/test_design_scaffold.py`
- `helix review --uncommitted`
- `helix plan lint`
- `git diff --stat .claude/settings.json`

## §11 carry

- component schemas (`$ref`) 解決は別 PLAN
