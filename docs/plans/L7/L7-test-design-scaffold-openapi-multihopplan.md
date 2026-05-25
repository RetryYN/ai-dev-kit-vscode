---
plan_id: L7-test-design-scaffold-openapi-multihopplan
title: "L7-test-design-scaffold-openapi-multihopplan: OpenAPI 2-hop $ref 解決"
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
    slot_label: "SE — _resolve_openapi_ref の multi-hop 解決と循環安全化"
  - role: qa
    slot_label: "QA — pytest / py_compile / review / plan lint verification"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-openapi-multihopplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`_resolve_openapi_ref()` を 1-hop 限定から 2-hop/3-hop 再帰解決へ拡張し、循環参照と hop 上限超過でも例外を出さず最後に到達した dict を返す。

## §1 背景

- W32 までで local `$ref` の 1-hop 解決は入っているが、`components.schemas.A -> B` のような 2-hop 参照では detail が欠落する
- carry に残っていた deep ref / circular ref の安全化をここで最小スコープで回収する
- 既存 43 pytest と 1-hop default 挙動は維持し、互換性を崩さず helper 内部だけを拡張する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `_resolve_openapi_ref(spec, ref_str, *, max_hops=3, visited=None) -> dict` へ拡張
   - local `$ref` を再帰で最大 3-hop まで解決する
   - `visited` set で循環検出し、循環時は最後の dict を返す
   - `max_hops` 超過時は最後の dict を返す
2. `cli/lib/tests/test_test_design_scaffold.py`
   - 2-hop resolve / circular / max_hops 超過の pytest 3 件を追加する

scope 外:

- OpenAPI remote ref 解決
- `allOf` / `oneOf` / `anyOf` merge
- response schema の deep normalization

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | multi-hop / circular-safe helper 実装 | pytest 46/46 PASS / py_compile PASS | draft |
| .3 | 検証 + review + lint | `helix review --uncommitted` 実施 / plan lint PASS / settings 0 diff | draft |

## §11 carry 解消

- `L7-test-design-scaffold-openapi-refplan` §11 の「深い schema merge と循環参照解決は次 carry」を multi-hop safe resolve に限定して解消する
