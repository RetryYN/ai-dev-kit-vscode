---
doc_id: L6-FUNCTIONAL-DESIGN-FR-PLAN-01
title: PLAN dependency / generates trace 機能仕様
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
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - docs/v2/L6-functional-design/FR-TDD-01/function-spec.md
  - docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md
  - HELIX-workflows/helix-process/db-auto-registration.md
  - HELIX-workflows/helix-process/db-integration.md
artifact_type: design_doc
---

# PLAN dependency / generates trace 機能仕様

## 1. 目的

PLAN dependency / generates trace は、PLAN frontmatter と生成成果物を parse し、`plan_registry`、依存関係、生成物、参照、レビュー、agent slots へ正規化して、工程順序・TDD順序・影響範囲分析・DB feedback の共通入力にする機能である。

本仕様は L6 機能設計として、L1/L3 の PLAN 管理要件、L4 Plan and Gate Control、既存 `posttooluse-plan-auto-register.sh` / `plan_parser.py` / `plan_registry.py` の設計境界を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、実装、hook 変更、DB schema migration は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-12` / `FR-PLAN-01` | PLAN dependency / generates trace |
| `FR-TDD-01` | PLAN の step / allowed_files / evidence を TDD順序判定へ渡す |
| `FR-IMPACT-01` | PLAN dependency / generates を impact graph へ渡す |
| `FR-INV-01` | PLAN / generated artifact を asset inventory へ渡す |
| DB auto-registration | PLAN / ADR の保存を `plan_registry` へ upsert |
| DB-backed evidence lifecycle | auto-registration finding を events / metrics / feedback へ append |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| PLAN-FN-01 | `parse_plan_frontmatter(path)` | PLAN / ADR markdown path | parsed frontmatter | parse 失敗を成功扱いにしない。warning を保持する |
| PLAN-FN-02 | `normalize_plan_record(frontmatter, path)` | parsed frontmatter | normalized plan record | plan_id / kind / layer / process_layer / status / owner を保持する |
| PLAN-FN-03 | `extract_plan_edges(record)` | normalized plan record | dependency / generates / blocks / parent / reference edges | edge は source / target / relation / required を持つ |
| PLAN-FN-04 | `upsert_plan_registry(record, edges)` | record, edges, DB adapter | registry write result | idempotent。既存 row を重複作成しない |
| PLAN-FN-05 | `detect_plan_graph_cycle(edges)` | dependency graph | cycle finding | cycle は fail-close candidate。黙殺しない |
| PLAN-FN-06 | `emit_plan_auto_register_feedback(result)` | upsert result, cycle finding | events / metrics / feedback payload | append-only。auto-register 成功だけでは closure 不可 |
| PLAN-FN-07 | `emit_plan_guard_summary(result)` | registry result, strict full-flow status | goal audit summary | L6設計閉塞と full objective completion を分離する |

## 4. Output Contract

```yaml
plan_trace_record:
  plan_id: string
  path: string
  kind: string
  layer: L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | L14
  process_layer: string
  status: draft | in_progress | ready_for_review | completed | blocked | superseded
  generates:
    - artifact_path: string
      artifact_type: string
  dependencies:
    parent: string
    requires: []
    blocks: []
  edges:
    - source: string
      target: string
      relation: parent | requires | blocks | generates | references | reviews | agent_slot
      required: bool
  registry:
    upserted: bool
    idempotency_key: string
    cycle_detected: bool
  feedback:
    append_only: true
    candidate_generated: bool
    closure_allowed: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| frontmatter parse 失敗 | `parse_error` finding |
| plan_id / layer / process_layer 欠落 | `missing_required_field` |
| generates path が工程外 | `wrong_layer_generated_artifact` |
| dependency cycle | `cycle_detected` + block candidate |
| upsert 成功のみ | registration evidence。closure 不可 |
| posttooluse hook 通知のみ | candidate。closure 不可 |
| DB write failure | warning / blocked は policy に従うが、成功として記録しない |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| PLAN-UT-CAND-01 | PLAN-FN-01 | frontmatter parse error を warning / finding として保持する |
| PLAN-UT-CAND-02 | PLAN-FN-02 | required field 欠落を成功扱いしない |
| PLAN-UT-CAND-03 | PLAN-FN-03 | dependency / generates edge を source / target / relation 付きで返す |
| PLAN-UT-CAND-04 | PLAN-FN-04 | upsert は idempotent で重複 row を作らない |
| PLAN-UT-CAND-05 | PLAN-FN-05 | cycle を block candidate として検出する |
| PLAN-UT-CAND-06 | PLAN-FN-06 | auto-register feedback を closure に昇格しない |
| PLAN-UT-CAND-07 | PLAN-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-PLAN-01/unit-test-design.md` は現在タスクでは作成しない。
- `PLAN-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- hook 変更、DB auto-registration 実行、schema migration、CI/equivalent 接続、doctor fail-close 昇格は別 PLAN / 承認 / allowed_files / verification commands が必要である。
