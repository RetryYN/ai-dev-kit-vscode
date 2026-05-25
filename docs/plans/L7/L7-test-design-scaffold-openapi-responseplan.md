---
plan_id: L7-test-design-scaffold-openapi-responseplan
title: "L7-test-design-scaffold-openapi-responseplan: OpenAPI response schema を generate_skeleton へ反映"
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
    - docs/plans/L7/L7-test-design-scaffold-openapi-refplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — response 抽出拡張と skeleton expected responses 出力"
  - role: qa
    slot_label: "QA — pytest / py_compile / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-openapi-responseplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`extract_openapi_endpoints()` の `responses` を status code のみから description / schema_ref を含む entry へ拡張し、`generate_skeleton()` の OpenAPI endpoint TC に expected responses を表示する。

## §1 背景

- W32 までで parameter / requestBody の detail は抽出済みだが、response 側は status code のみで情報量が不足している
- `generate_skeleton()` の OpenAPI TC でも response expectation をそのまま test design へ引き継げていない
- 既存 40 pytest を壊さないため、`responses` は legacy `str` entry を許容する backward compat を維持する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `responses` entry を `str | dict` 互換に拡張する
   - 各 response から `status` / `description` / `schema_ref` を抽出する
   - OpenAPI endpoint TC の末尾に `expected responses:` を追加する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - response description / schema ref / TC 出力の pytest 3 件を追加する
   - 既存 assertions は status 比較へ寄せて互換性を保つ

scope 外:

- response schema 本体の deep merge / 展開
- `allOf` / `oneOf` / `anyOf` の解釈
- response example の詳細整形

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | response 抽出と skeleton 出力実装 | pytest 43/43 PASS / py_compile PASS | draft |
| .3 | 検証 + review + lint | `helix review --uncommitted` 実施 / plan lint PASS / settings 0 diff | draft |

## §11 carry 解消

- `L7-test-design-scaffold-openapi-ref` の carry だった response schema 表示不足を本 PLAN で解消する
