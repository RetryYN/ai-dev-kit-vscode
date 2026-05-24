---
plan_id: L7-route-engine-drift-type-retrofit-ext
doc_id: L7-route-engine-drift-type-retrofit-ext-design
title: "L7 route engine drift_type/Retrofit 拡張 設計"
status: completed
artifact_role: "① 設計 (V-model 4 artifact のうち)"
created: 2026-05-25
revised: 2026-05-25
owner: SE
related_docs:
  - docs/plans/L7/L7-route-engine-drift-type-retrofit-extplan.md
  - HELIX-workflows/helix-process/detection-routing.md
  - docs/v2/L7-test-design/L7-route-engine-drift-type-retrofit-ext-test-design.md
phases: L7
gates: G6,G7
---

# L7 route engine drift_type/Retrofit 拡張 設計

## §0 概要

本書は `L7-route-engine-drift-type-retrofit-ext` の ① 設計 artifact である。親設計 `HELIX-workflows/helix-process/detection-routing.md` を変更せず、`cli/lib/route_engine.py` と `cli/helix-route` に対して route 契約の拡張を追補する。

- 対象実装: `cli/lib/route_engine.py`, `cli/helix-route`
- 対応 ③ テスト設計: `docs/v2/L7-test-design/L7-route-engine-drift-type-retrofit-ext-test-design.md`
- 対応 ④ テストコード: `cli/lib/tests/test_route_engine.py`, `cli/tests/helix-route.bats`

## §1 設計判断

### 1.1 Mode/Kind 拡張

- `Mode` に `Retrofit` を追加する
- `Kind` に `retrofit` を追加する
- 既存 signal の mode/kind は保持し、追加は additive に留める

### 1.2 drift_type 7 種

`drift` signal は次の 7 種へ細分化する。

| drift_type | mode | kind | subtype |
|---|---|---|---|
| `schema` | Reverse | reverse | normalization |
| `contract` | Reverse | reverse | normalization |
| `code_smell` | Refactor | refactor | - |
| `structural` | Refactor | refactor | - |
| `dependency_outdated` | Retrofit | retrofit | dependency |
| `upgrade` | Retrofit | retrofit | upgrade |
| `config_drift` | Retrofit | retrofit | config |

- `drift` で `drift_type` 未指定時は `schema` を既定値とする
- shortcut signal `dependency_outdated` / `upgrade` / `config_drift` は `drift_type` を自動付与する
- shortcut signal と矛盾する `drift_type` 明示指定は `RouteEngineError` で fail-close とする

### 1.3 recommended_command 契約

`RouteResult` に `recommended_command` を JSON object で追加する。機械契約は次で統一する。

| route | command | args |
|---|---|---|
| Reverse(normalization) | `helix reverse normalization R0` | `{}` |
| Reverse(code) | `helix reverse code R0` | `{}` |
| Refactor | `helix plan draft` | `{"kind":"refactor"}` |
| Retrofit | `helix plan draft` | `{"kind":"retrofit","drift_type":"..."}` |
| Recovery / Incident(prod) | `helix recover plan` | `{"signal_id":"...","reopen_point":"...","auto_routed_from":"helix-route"}` |

`recommended_command.safety` は `auto_apply` / `requires_human_approval` / `requires_preflight` の 3 field のみ持つ。

- `upgrade` かつ `uncertainty=high` または `impact=high` の場合は `helix reverse upgrade R0` を preflight として返す
- `config_drift` は `requires_human_approval=true` とする

### 1.4 suggest/eval の役割分離

- `helix route eval` は既存どおり full `RouteResult` を返し、`--format command` では `suggest_command` のみ返す
- `helix route suggest` はデフォルトで人間向けの `suggest_command` 1 行を返し、`--format json` または `--json` で full `RouteResult` を返す
- `suggest_command` は backward compatibility 用の string として維持し、機械処理は `recommended_command` を使う

### 1.5 signal inventory

- `list_signals()` は新 signal 3 種を列挙する
- `drift` エントリには `drift_types[]` を追加し、利用可能な細分類を可視化する

## §2 実装境界

- 変更対象: `cli/lib/route_engine.py`, `cli/helix-route`, `cli/lib/tests/test_route_engine.py`, `cli/tests/helix-route.bats`
- 変更しない: `HELIX-workflows/helix-process/detection-routing.md`, detector registry, recover/reverse CLI 本体

## §3 Trace

- ① 本書 → ② 実装コード: `cli/lib/route_engine.py`, `cli/helix-route`
- ① 本書 → ③ テスト設計: `docs/v2/L7-test-design/L7-route-engine-drift-type-retrofit-ext-test-design.md`
- ③ テスト設計 → ④ テストコード: `cli/lib/tests/test_route_engine.py`, `cli/tests/helix-route.bats`
- ④ テストコード → ③ テスト設計: 各 test docstring / Bats case が `U-EXT-*` / `B-EXT-*` に対応する
