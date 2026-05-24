---
plan_id: L7-route-engine-drift-type-retrofit-ext
doc_id: L7-route-engine-drift-type-retrofit-ext-test-design
title: "L7 route engine drift_type/Retrofit 拡張 テスト設計"
status: completed
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-25
revised: 2026-05-25
owner: SE
related_docs:
  - docs/plans/L7/L7-route-engine-drift-type-retrofit-extplan.md
  - docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md
phases: L7
gates: G6,G7
---

# L7 route engine drift_type/Retrofit 拡張 テスト設計

## §0 概要

本書は `L7-route-engine-drift-type-retrofit-ext` の ③ テスト設計 artifact であり、① 設計・② 実装コード・④ テストコードとは分離して管理する。

- 対象 PLAN: `docs/plans/L7/L7-route-engine-drift-type-retrofit-extplan.md`
- 対応 ① 設計 doc: `docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md`
- 対応 ② 実装コード: `cli/lib/route_engine.py`, `cli/helix-route`
- 対応 ④ テストコード: `cli/lib/tests/test_route_engine.py`, `cli/tests/helix-route.bats`

本テスト設計は drift signal の 7 種分岐、`Retrofit` mode 追加、`recommended_command` JSON object 契約、`helix route suggest` CLI surface の 4 点を固定する。

## §1 テスト対象

| 対象 | 責務 |
|---|---|
| `RouteEngine.evaluate()` | signal / drift_type / env から route を確定する |
| `RouteEngine.from_detect_output()` | detect JSON から drift_type を伝播する |
| `RouteEngine.list_signals()` | 新 signal と `drift_types[]` を公開する |
| `cli/helix-route suggest` | 人間向け string と機械向け JSON の両出力を提供する |

## §2 単体テスト設計

### U-EXT-001-U-EXT-008 drift signal の 7 種分岐と backward compat

- `signal=drift` + `drift_type=schema|contract` は `Reverse/reverse/normalization`
- `signal=drift` + `drift_type=code_smell|structural` は `Refactor/refactor`
- `signal=drift` + `drift_type=dependency_outdated|upgrade|config_drift` は `Retrofit/retrofit`
- `signal=drift` + `drift_type` 未指定は `schema` 扱いで `Reverse/reverse/normalization`

### U-EXT-009-U-EXT-013 shortcut signal と drift_type 自動付与

- `dependency_outdated`, `upgrade`, `config_drift` は shortcut signal として `drift_type` を自動付与する
- `unknown_design` など非 drift/非 shortcut signal は `drift_type=None`

### U-EXT-014-U-EXT-017 recommended_command 契約

- `Retrofit` は `{"command":"helix plan draft","args":{"kind":"retrofit","drift_type":"..."}}`
- `Reverse` は `{"command":"helix reverse normalization R0","args":{}}`
- `Refactor` は `{"command":"helix plan draft","args":{"kind":"refactor"}}`
- `safety` は `auto_apply` / `requires_human_approval` / `requires_preflight` の 3 field のみ
- `RouteResult.to_dict()` に `drift_type` / `recommended_command` を含める

### U-EXT-018-U-EXT-019 detect JSON 伝播

- `result.drift_type` 指定時は `RouteResult.drift_type` に反映する
- 指定なしは `drift` のみ `schema` を既定値にする

### U-EXT-020-U-EXT-021 signal inventory 拡張

- `list_signals()` は `dependency_outdated` / `upgrade` / `config_drift` を含む
- `drift` エントリは `drift_types[]` を公開する

### U-EXT-022-U-EXT-026 互換性と fail-close

- 既存の `drift -> Reverse/normalization` 振る舞いは維持する
- high risk `upgrade` は `helix reverse upgrade R0` を preflight として返す
- shortcut signal と矛盾する `drift_type` 明示指定は `RouteEngineError` にする

## §3 CLI/Bats テスト設計

| Case ID | 観点 | 期待結果 |
|---|---|---|
| B-EXT-001 | `helix route eval --signal drift` | 既存どおり `Reverse` |
| B-EXT-002 | `helix route eval --signal dependency_outdated` | JSON に `mode=Retrofit`, `drift_type=dependency_outdated` |
| B-EXT-003 | `helix route suggest --signal dependency_outdated` | stdout は `suggest_command` の 1 行 string |
| B-EXT-004 | `helix route suggest --signal drift --drift-type config_drift` | Retrofit 向け 1 行 string |
| B-EXT-005 | `helix route suggest --signal drift --drift-type code_smell` | Refactor 向け 1 行 string |
| B-EXT-006 | `helix route suggest --signal drift` | drift_type 未指定でも backward compat で Reverse string |
| B-EXT-007 | `helix route list-signals --json` | 新 signal 3 種 + `drift_types[]` を含む |
| B-EXT-008 | `helix route suggest --format json` | `recommended_command` JSON object を含む RouteResult |

## §4 Trace

- ① 設計 → ③ 本書: `docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md`
- ③ 本書 → ④ テストコード: `cli/lib/tests/test_route_engine.py`, `cli/tests/helix-route.bats`
- ④ テストコード → ③ 本書: 各 test docstring で `U-EXT-*` / `B-EXT-*` を参照する
