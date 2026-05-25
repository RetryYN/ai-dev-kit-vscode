---
plan_id: L7-test-design-scaffold-openapi-refplan
title: "L7-test-design-scaffold-openapi-refplan: OpenAPI $ref / component schemas 解決"
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
    - docs/plans/L7/L7-test-design-scaffold-openapi-schemaplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — OpenAPI $ref 解決 helper と endpoint 抽出拡張"
  - role: qa
    slot_label: "QA — pytest / py_compile / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-openapi-refplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`extract_openapi_endpoints()` に OpenAPI `$ref` 1-hop 解決を追加し、`parameters` / `requestBody` / `responses` 内の `#/components/...` 参照を安全に解決する。

## §1 背景

- W31 では OpenAPI parameter detail までは追加済みだが、`$ref` を含む一般的な spec では detail が落ちる
- 特に `components.parameters` と `components.schemas` を経由する spec で test scaffold の情報量が不足する
- 循環参照や深い再帰は今回 scope 外とし、1-hop のみ安全に解決する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `_resolve_openapi_ref(spec: dict, ref_str: str) -> dict` を追加する
   - `parameters` で `components.parameters` 参照を解決する
   - `requestBody.content.*.schema.$ref` を `components.schemas` から解決する
   - `responses` は status code 一覧維持のまま、内部 `$ref` があっても例外なく処理する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 件を追加し、parameter ref / request body ref / missing ref を固定する

scope 外:

- 2-hop 以上の再帰解決
- `allOf` / `oneOf` / `anyOf` merge
- schema 以外の OpenAPI object 全般の深い正規化

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | `$ref` helper と endpoint 抽出実装 | pytest 40/40 PASS / py_compile PASS | draft |
| .3 | 検証 + review + lint | review 実施 / plan lint PASS / settings 0 diff | draft |

## §11 carry

- 深い schema merge と循環参照解決は次 carry
