---
plan_id: L7-test-design-scaffold-openapi-detailplan
title: "L7-test-design-scaffold-openapi-detailplan: OpenAPI parameter/response detail extraction"
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
    - docs/plans/L7/L7-test-design-scaffold-openapiplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE - OpenAPI detail extraction and scaffold expansion"
  - role: qa
    slot_label: "QA - pytest / py_compile / lint / review verification"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-openapi-detailplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`extract_openapi_endpoints()` の各 entry に `parameters` / `responses` / `request_body` を追加し、`generate_skeleton(openapi_spec_path=...)` の `TC-OPENAPI-*` blockquote へ詳細を展開する。

## §1 scope

1. `cli/lib/test_design_scaffold.py`
   - entry dict を `{method, path, summary, parameters, responses, request_body}` へ拡張
   - `parameters` は name のみ list、`responses` は status code のみ list、`request_body` は description または `present`
2. `cli/lib/tests/test_test_design_scaffold.py`
   - parameters / responses / missing detail の 3 test を追加
   - 既存 OpenAPI skeleton test を詳細表示期待に更新

scope 外:
- parameter schema の type/required/example 解釈
- CLI option 追加
- 既存 markdown endpoint 抽出契約変更

## §2 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + failing test 追加 | 3 test 追加、既存 skeleton 期待更新 | draft |
| .2 | OpenAPI detail extraction 実装 | pytest 34/34 PASS、py_compile PASS | draft |
| .3 | 検証 + review + lint | plan lint PASS、settings 0 diff | draft |

## §11 carry

- parameter schema 詳細解釈 (`type` / `required` / `example`) は別 PLAN
