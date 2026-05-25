---
plan_id: L7-test-design-scaffold-openapiplan
title: "L7-test-design-scaffold-openapiplan: OpenAPI endpoint test case scaffold"
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
    - docs/plans/L7/L7-test-design-scaffold-api-endpointplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — OpenAPI YAML/JSON 解析と skeleton 展開"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint / review 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-openapiplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

OpenAPI 3.x YAML / JSON spec から endpoint を抽出する `extract_openapi_endpoints()` helper を追加し、`generate_skeleton()` に `openapi_spec_path` を通して `TC-OPENAPI-001..N` を展開する。

## §1 背景

- W23 で markdown 内 endpoint 抽出は完成したが、外部 OpenAPI spec file からの抽出は未対応
- parent design doc 由来 endpoint と OpenAPI spec 由来 endpoint は独立 source として併用可能にする
- OpenAPI の `parameters` / `responses` 詳細抽出は本 wave の scope 外とし carry に分離する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `extract_openapi_endpoints(spec_path: Path, *, max_count: int = 10) -> list[dict[str, str]]` を追加
   - `yaml.safe_load` または `json.loads` で parse し、OpenAPI 3.x の `paths` 配下から `get/post/put/delete/patch` を列挙する
   - file 不在または parse error 時は空 list を返し、例外を外へ出さない
   - `generate_skeleton(..., openapi_spec_path: Path | str | None = None)` を追加し、指定時だけ `TC-OPENAPI-001..N` を展開する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 件を追加し、yaml parse・missing file・skeleton 展開を固定する

scope 外:

- CLI option 追加
- `parameters` / `responses` / request body の詳細抽出
- markdown endpoint 抽出ロジックの契約変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | `cli/lib/test_design_scaffold.py` OpenAPI helper 実装 | pytest 26/26 PASS / py_compile PASS | draft |
| .3 | 検証 + review + plan lint | review 実施 / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `extract_openapi_endpoints()` は OpenAPI 3.x spec の `paths` から HTTP method と path を抽出し、summary があれば含める
- `max_count` を超える endpoint は truncate する
- spec file 不在または parse error では空 list を返し、例外を出さない
- `generate_skeleton(..., openapi_spec_path=...)` は paired design doc 抽出と独立に動作し、両方併用できる
- OpenAPI endpoint 抽出結果があるとき、§2 に `TC-OPENAPI-001..N` を追加し、各 TC に method + path + summary を blockquote で含める
- 既存 23 pytest を壊さない

## §5 検証

- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `grep -c 'extract_openapi_endpoints\\|openapi_spec_path' cli/lib/test_design_scaffold.py`
- `helix plan lint`
- `git diff --stat .claude/settings.json`

## §11 carry

- OpenAPI の `parameters` / `responses` / request body 詳細抽出は別 PLAN
