---
plan_id: L7-test-design-scaffold-api-endpointplan
title: "L7-test-design-scaffold-api-endpointplan: API endpoint test case scaffold"
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
    - docs/plans/L7/L7-test-design-scaffold-function-schemaplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — API endpoint 抽出と skeleton 展開"
  - role: qa
    slot_label: "QA — pytest / py_compile / plan lint / review 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-api-endpointplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

parent design doc から API endpoint (HTTP method + path) を簡易抽出し、test design skeleton の §2 テストケースへ endpoint 別 TC-API-001..N 雛形を展開する。

## §1 背景

- function schema 抽出は既に実装済みだが、API doc は markdown table や `GET /api/x` 形式の記述が多く、別 helper が必要
- `generate_skeleton()` から endpoint 抽出を opt-in で有効化し、既存 default 挙動は崩さない
- OpenAPI YAML / JSON の構造解析は本 wave の scope 外とし、別 PLAN carry に分離する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `extract_api_endpoints(paired_design_path: Path, *, max_count: int = 5) -> list[dict[str, str]]` を追加
   - inline / markdown table から `(method, path)` を抽出する
   - `generate_skeleton(..., extract_endpoints: bool = False)` を追加
   - `extract_endpoints=True` のときだけ §2 に `TC-API-001..N` を endpoint 別に展開する
2. `cli/lib/tests/test_test_design_scaffold.py`
   - pytest 3 件を追加
   - 既存 20 件の挙動を維持する

scope 外:

- CLI option 追加
- bats 変更
- OpenAPI YAML / JSON の構造解析

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 case 追加 | PLAN 作成 / pytest fail で仕様固定 | draft |
| .2 | `cli/lib/test_design_scaffold.py` 実装拡張 | pytest 23/23 PASS / py_compile PASS | draft |
| .3 | 検証 + review + plan lint | review 実施 / plan lint PASS / settings 0 diff | draft |

## §4 受入条件

- `extract_api_endpoints()` は inline 記法と markdown table row から endpoint を最大 `max_count` 件まで抽出する
- paired design doc 不在時は空 list を返し、例外を出さない
- `generate_skeleton(..., extract_endpoints=False)` の既定挙動は維持する
- `extract_sections` / `extract_functions` / `extract_endpoints` は独立に機能する
- `extract_endpoints=True` かつ抽出結果ありのとき、§2 に `TC-API-001..N` を endpoint 別に展開し、各 TC に method + path を blockquote で含める

## §5 検証

- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `grep -c 'extract_api_endpoints\\|extract_endpoints' cli/lib/test_design_scaffold.py`
- `helix plan lint`
- `git diff --stat .claude/settings.json`

## §11 carry

- OpenAPI YAML / JSON の構造解析は別 PLAN
