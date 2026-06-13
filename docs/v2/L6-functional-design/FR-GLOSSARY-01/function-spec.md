---
doc_id: L6-FUNCTIONAL-DESIGN-FR-GLOSSARY-01
title: ドメイン用語 SSoT + 自動チェック 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-12
parent_requirements:
  - docs/v2/L0-helix-workflows/concept.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/物理データ設計.md
related_design:
  - docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
  - docs/v2/L6-functional-design/FR-INV-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DOCREVIEW-01/function-spec.md
artifact_type: design_doc
---

# ドメイン用語 SSoT + 自動チェック 機能仕様

## 1. 目的

ドメイン用語 SSoT + 自動チェックは、L0 §12 Glossary と機械可読 DDD registry を基準に、HELIX-workflows 全工程 doc、PLAN、skill、commit message の用語ゆれ、未定義語、anti-corruption layer 違反を検出する機能である。

本仕様は L6 機能設計として、L3 `FR-GLOSSARY-01` と L4 registry-only 機能を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、`helix glossary` CLI 実装、DB table 化、schema migration は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-GLOSSARY-01` | 用語 SSoT と自動チェック |
| L0 §12 Glossary | 用語定義の原本 |
| `FR-INV-01` | 用語 registry を asset inventory に接続する |
| `FR-DOCREVIEW-01` | doc-review の Consistency / DDD SSoT 観点に用語結果を渡す |
| `FR-FNREG-01` | FR-* 命名と用語 registry の整合を参照する |
| DDD registry detector | glossary / bounded context / anti-corruption の既存 detector contract |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| GLOSS-FN-01 | `load_glossary_registry(registry_path, concept_path)` | DDD registry, L0 concept | normalized glossary entries | L0 §12 を原本とし、mirror を原本化しない |
| GLOSS-FN-02 | `list_glossary(scope)` | scope: L0 / L1 / L3 / all | term summary list | Bounded Context 固有語と全体語を分離する |
| GLOSS-FN-03 | `show_glossary_term(term)` | term | definition / source / related CLI / schema field | 未定義 term は空成功にしない |
| GLOSS-FN-04 | `check_glossary_usage(docs, glossary)` | docs, glossary entries | undefined / variant / missing reference findings | 未定義用語を正常扱いしない |
| GLOSS-FN-05 | `check_anti_corruption_boundary(docs, bounded_contexts)` | docs, BC registry | boundary violation findings | 子 doc の独自定義を許可済み写像なしに通さない |
| GLOSS-FN-06 | `emit_glossary_doc_review_input(findings)` | findings | doc-review / doctor input | Consistency / DDD SSoT 観点を失わない |
| GLOSS-FN-07 | `append_glossary_feedback(findings)` | findings, evidence refs | events / metrics / feedback payload | append-only。candidate を closure にしない |
| GLOSS-FN-08 | `emit_glossary_completion_guard_summary(state)` | state, strict full-flow status | goal audit summary | L6設計閉塞と L7実装完了を分離する |

## 4. Output Contract

```yaml
glossary_check_report:
  scope: L0 | L1 | L3 | all
  source_of_truth: docs/v2/L0-helix-workflows/concept.md#12-glossary
  registry_mirror: cli/config/ddd-registry.yaml
  terms:
    - term: string
      definition_source: string
      bounded_context: string
      implementation_status: installed | partial | L4-carry | not-implemented
      grep_pattern: string
  findings:
    - type: undefined_term | term_variant | anti_corruption_violation | registry_mirror_drift | missing_reference
      severity: P0 | P1 | P2 | P3
      term: string
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
| doc 内用語が L0 §12 / registry に存在しない | `undefined_term` |
| 同義語や表記ゆれが許可済み alias なしに出る | `term_variant` |
| Bounded Context 固有語を Glossary 経由せず別 context へ持ち込む | `anti_corruption_violation` |
| L0 §12 と DDD registry mirror がずれる | `registry_mirror_drift` |
| 用語 entry に CLI / file path / schema field / grep pattern が無い | `missing_reference` |
| registry-only entry | L6仕様化は可能、L7実装完了にはしない |
| findings append のみ | candidate。closure 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| GLOSS-UT-CAND-01 | GLOSS-FN-01 | L0 §12 を原本として mirror drift を検出する |
| GLOSS-UT-CAND-02 | GLOSS-FN-02 | BC 固有語と全体語を分離する |
| GLOSS-UT-CAND-03 | GLOSS-FN-03 | 未定義 term を空成功にしない |
| GLOSS-UT-CAND-04 | GLOSS-FN-04 | undefined / variant を検出する |
| GLOSS-UT-CAND-05 | GLOSS-FN-05 | anti-corruption violation を検出する |
| GLOSS-UT-CAND-06 | GLOSS-FN-06 | doc-review / doctor input に DDD 観点を保持する |
| GLOSS-UT-CAND-07 | GLOSS-FN-07 | feedback append を closure に昇格しない |
| GLOSS-UT-CAND-08 | GLOSS-FN-08 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-GLOSSARY-01/unit-test-design.md` は現在タスクでは作成しない。
- `GLOSS-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- `helix glossary` CLI、doctor fail-close 昇格、DB table 化、CI/equivalent 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
