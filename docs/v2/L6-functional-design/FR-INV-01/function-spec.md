---
doc_id: L6-FUNCTIONAL-DESIGN-FR-INV-01
title: 資産 inventory / density 可視化 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
parent_requirements:
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/registry-detector-機能設計.md
  - docs/v2/L6-functional-design/coding-rule-detector-機能設計.md
  - docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - HELIX-workflows/helix-process/asset-mapping.md
  - HELIX-workflows/helix-process/db-auto-registration.md
artifact_type: design_doc
---

# 資産 inventory / density 可視化 機能仕様

## 1. 目的

資産 inventory / density 可視化は、skill、CLI、PLAN、docs、DB schema、registry、hook を L0-L14 工程へ双方向 mapping し、未登録資産、過密工程、未整備工程、実装状態 drift を機械検出する機能である。

本仕様は L6 機能設計として、L1 FR-09 / L3 FR-INV-01 / L4 Asset and Knowledge Governance を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、実装、DB schema migration、hook 変更は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-09` / `FR-INV-01` | 資産 inventory / density 可視化 |
| `FR-FNREG-01` | functional-registry の中央 SSoT |
| `FR-GLOSSARY-01` | DDD / 用語 SSoT |
| coding-rule detector | coding-rule registry の自己登録漏れ検出 |
| DDD registry detector | glossary / bounded context registry の drift 検出 |
| DB-backed evidence lifecycle | inventory finding を events / metrics / feedback へ append |
| HARNESS external tools | 外部 tool candidate を inventory / impact graph に接続 |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| INV-FN-01 | `collect_asset_inventory(repo_root)` | repo root, known source dirs | asset list | read-only。生成物やテスト一時ファイルを active asset と誤認しない |
| INV-FN-02 | `normalize_asset_record(asset)` | path, kind, layer hint, registry refs | normalized asset | path / kind / source_registry / implementation_status を必須にする |
| INV-FN-03 | `map_asset_to_layer(asset, registries)` | normalized asset, functional / coding / DDD registries | layer mapping | L6 逃げ防止として coverage_layer と design_id を分離する |
| INV-FN-04 | `detect_unregistered_assets(mapped_assets)` | mapped assets, registry entries | findings | registry に無い active asset を warning / blocking 候補として返す |
| INV-FN-05 | `compute_density_by_layer(mapped_assets)` | mapped assets | density summary | 工程別 count / bucket / unknown を返す。unknown を正常扱いしない |
| INV-FN-06 | `append_inventory_feedback(findings)` | findings, evidence refs | events / metrics / feedback payload | append-only。snapshot だけでは closure 不可 |
| INV-FN-07 | `emit_inventory_guard_summary(summary)` | density summary, strict full-flow status | goal audit summary | L6設計閉塞と full objective completion を混同しない |

## 4. Output Contract

```yaml
asset_inventory_summary:
  collected_at: ISO8601
  assets:
    - path: string
      kind: cli | lib | hook | skill | doc | plan | registry | db_schema | test | template
      process_layer: L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | L14 | unknown
      coverage_layer: L4 | L5 | L6 | excluded_with_reason | unknown
      design_id: string
      source_registry: functional | coding_rule | ddd | plan_registry | inferred | none
      implementation_status: installed | partial | L4-carry | not-implemented
  findings:
    - type: unregistered_asset | missing_design_id | unknown_layer | density_gap | registry_drift
      severity: P0 | P1 | P2 | P3
      path: string
      required_next: string
  feedback:
    append_only: true
    candidate_generated: bool
    closure_allowed: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| active asset に registry entry が無い | `unregistered_asset` |
| `coverage_layer=L6_required` だが design_id が無い | `missing_design_id` |
| process_layer が不明 | `unknown_layer` |
| registry の path が存在しない | `registry_drift` |
| coding-rule / DDD registry 自体が functional-registry に無い | `self_asset_reverse_leak` |
| inventory finding のみ | candidate。closure 不可 |
| feedback append のみ | candidate。closure 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| INV-UT-CAND-01 | INV-FN-01 | active asset と生成物 / 一時ファイルを区別する |
| INV-UT-CAND-02 | INV-FN-02 | path / kind / implementation_status 欠落を finding 化する |
| INV-UT-CAND-03 | INV-FN-03 | coverage_layer と design_id を分離して保持する |
| INV-UT-CAND-04 | INV-FN-04 | registry 未登録 asset を検出する |
| INV-UT-CAND-05 | INV-FN-05 | layer density と unknown count を返す |
| INV-UT-CAND-06 | INV-FN-06 | feedback append を closure に昇格しない |
| INV-UT-CAND-07 | INV-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-INV-01/unit-test-design.md` は現在タスクでは作成しない。
- `INV-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- registry 更新、DB auto-registration 実行、doctor fail-close 昇格、CI/equivalent 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
