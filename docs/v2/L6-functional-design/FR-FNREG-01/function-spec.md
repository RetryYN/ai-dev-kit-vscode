---
doc_id: L6-FUNCTIONAL-DESIGN-FR-FNREG-01
title: 機能一覧 SSoT + 自動チェック 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-12
parent_requirements:
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/物理データ設計.md
related_design:
  - docs/v2/L6-functional-design/functional-registry-detector-機能設計.md
  - docs/v2/L6-functional-design/FR-INV-01/function-spec.md
  - docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md
artifact_type: design_doc
---

# 機能一覧 SSoT + 自動チェック 機能仕様

## 1. 目的

機能一覧 SSoT + 自動チェックは、HELIX-workflows の FR 定義と実在資産を `functional-registry` として正本化し、doc 内の FR 参照、未定義 ID、重複 ID、実装状態 drift を検出する機能である。

本仕様は L6 機能設計として、L3 `FR-FNREG-01` と L4 registry-only 機能を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、`helix function registry` CLI 実装、DB table 化、schema migration は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-FNREG-01` | FR-* 中央 SSoT と自動チェック |
| `FR-INV-01` | asset inventory から registry entry を参照する |
| `FR-GLOSSARY-01` | FR-* 命名と用語 SSoT の整合を参照する |
| `FR-CHANGEPROP-01` | 上流変更時の下流 FR trace と balance regression 判定に使う |
| `functional-registry-detector` | 既存 detector contract / yaml schema / warn-only report |
| `L3 functional registry` | FR 定義、資産一覧、coverage_layer、design_ids の SSoT |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| FNREG-FN-01 | `load_function_registry(registry_path)` | functional-registry yaml / md source | normalized registry entries | 必須 field 欠落を黙殺しない。read-only |
| FNREG-FN-02 | `list_function_registry(scope)` | scope: L1 / L3 / L4 / L6 / all | FR summary list | registry-only と code-backed を混同しない |
| FNREG-FN-03 | `show_function_entry(fr_id)` | FR-ID | definition source / status / related artifacts | 未定義 ID は空成功にしない |
| FNREG-FN-04 | `check_fr_reference_alignment(docs, registry)` | docs, registry entries | drift / undefined / duplicate findings | 未定義 FR 0 件を合格条件にする |
| FNREG-FN-05 | `check_registry_asset_alignment(registry, repo_root)` | registry entries, repo paths | missing path / reverse leak findings | deprecated / excluded は理由付きで分離する |
| FNREG-FN-06 | `emit_fnreg_doctor_input(findings)` | findings | doctor / gate input | P0/P1 を advisory に降格しない |
| FNREG-FN-07 | `append_fnreg_feedback(findings)` | findings, evidence refs | events / metrics / feedback payload | append-only。candidate を closure にしない |
| FNREG-FN-08 | `emit_fnreg_completion_guard_summary(state)` | state, strict full-flow status | goal audit summary | L6設計閉塞と L7実装完了を分離する |

## 4. Output Contract

```yaml
function_registry_report:
  scope: L1 | L3 | L4 | L6 | all
  source_registry: cli/config/functional-registry.yaml | docs/v2/L3-requirements/helix-workflows-functional-registry.md
  entries:
    - fr_id: string
      name: string
      definition_source: string
      bucket: code | registry-only | deprecated | excluded_with_reason
      implementation_status: installed | partial | L4-carry | not-implemented
      coverage_layer: L4_required | L5_required | L6_required | excluded_with_reason
      design_ids: []
  findings:
    - type: undefined_fr | duplicate_fr | registry_drift | missing_asset | reverse_leak | status_mismatch
      severity: P0 | P1 | P2 | P3
      fr_id: string
      path: string
      required_next: string
  completion:
    l6_design_gap_closed: bool
    l7_artifact_created_in_current_scope: false
    goal_completion_allowed: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| doc 内 FR 参照が registry に存在しない | `undefined_fr` |
| 同一 FR-ID が複数定義される | `duplicate_fr` |
| L3 registry と machine registry の name / count が違う | `registry_drift` |
| active entry の path が存在しない | `missing_asset` |
| repo に存在する active asset が registry に無い | `reverse_leak` |
| `implementation_status` が実在証跡と矛盾する | `status_mismatch` |
| registry-only entry | L6仕様化は可能、L7実装完了にはしない |
| findings append のみ | candidate。closure 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| FNREG-UT-CAND-01 | FNREG-FN-01 | 必須 field 欠落を fail-close する |
| FNREG-UT-CAND-02 | FNREG-FN-02 | registry-only と code-backed を区別する |
| FNREG-UT-CAND-03 | FNREG-FN-03 | 未定義 FR-ID を空成功にしない |
| FNREG-UT-CAND-04 | FNREG-FN-04 | undefined / duplicate FR を検出する |
| FNREG-UT-CAND-05 | FNREG-FN-05 | missing path と reverse leak を分離する |
| FNREG-UT-CAND-06 | FNREG-FN-06 | P0/P1 を doctor input で保持する |
| FNREG-UT-CAND-07 | FNREG-FN-07 | feedback append を closure に昇格しない |
| FNREG-UT-CAND-08 | FNREG-FN-08 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-FNREG-01/unit-test-design.md` は現在タスクでは作成しない。
- `FNREG-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- `helix function registry` CLI、doctor fail-close 昇格、DB table 化、CI/equivalent 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
