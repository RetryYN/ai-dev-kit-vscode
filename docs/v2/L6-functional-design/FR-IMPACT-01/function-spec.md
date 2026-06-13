---
doc_id: L6-FUNCTIONAL-DESIGN-FR-IMPACT-01
title: 影響範囲 query 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
parent_requirements:
  - docs/v2/L0-helix-workflows/concept.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md
  - HELIX-workflows/helix-process/db-auto-registration.md
  - HELIX-workflows/helix-process/cross-detection.md
  - HELIX-workflows/helix-process/detection-routing.md
artifact_type: design_doc
---

# 影響範囲 query 機能仕様

## 1. 目的

影響範囲 query は、機能改修・障害対応・外部ツール finding を起点に、関連する PLAN、設計、テスト設計、実装ファイル、DB / schema、gate、feedback を 5 秒以内に取得し、「ここだけ直す」か「広めに直す」かを機械判定する機能である。

本仕様は L6 機能設計として、L0 の dependency graph + trace_link 構想、L1 BR-06、L3 FR-IMPACT-01、L4/L5 の内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、実装、DB schema migration、CI 接続、外部ツール実行は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `BR-06` | 影響範囲 query 応答時間 5 秒以内 |
| `FR-IMPACT-01` | artifact / event / trace / dependency graph を横断する query |
| `FR-INV-01` | skill / CLI / PLAN / docs / DB schema の inventory |
| `FR-PLAN-01` | PLAN dependency / generates / allowed_files |
| `FR-EVT-01` | mode closure / L7 run / feedback event |
| `DBEV-FN-*` | evidence lifecycle と feedback append |
| `HEXT-FN-*` | external tool finding から impact graph を構築 |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| IMPACT-FN-01 | `normalize_impact_seed(seed)` | plan_id / artifact path / symbol / schema object / detector finding | normalized seed | seed 種別を保持し、解決不能でも空 seed にしない |
| IMPACT-FN-02 | `collect_trace_neighbors(seed, repo_root)` | normalized seed, registry, plan frontmatter, trace docs | trace neighbor set | read-only。存在しない doc / code を生成済みにしない |
| IMPACT-FN-03 | `collect_dependency_edges(neighbors)` | plan dependency, registry links, DBEV/HEXT impact refs | dependency edge list | source -> target -> relation -> confidence を持つ |
| IMPACT-FN-04 | `rank_impact_scope(edges, evidence)` | edges, change set size, centrality, coverage state | local / broad / unknown | unknown を local と偽装しない |
| IMPACT-FN-05 | `render_impact_query_result(scope)` | ranked scope, evidence refs | machine JSON + human summary | PLAN / design / test-design / code / gate / feedback を分けて返す |
| IMPACT-FN-06 | `append_impact_feedback(result)` | result, source finding | events / metrics / feedback payload | append-only。query result だけでは closure 不可 |
| IMPACT-FN-07 | `emit_impact_guard_summary(result)` | query result, strict full-flow status | goal audit summary | L6 design closure と full objective completion を分離する |

## 4. Query State Machine

```yaml
impact_query_state:
  states:
    - seed_received
    - trace_resolved
    - dependency_edges_built
    - scope_ranked
    - result_rendered
    - feedback_appended
  terminal_verdict:
    local:
      meaning: affected nodes are bounded and required gates are known
    broad:
      meaning: central nodes, schema/API boundary, or cross-layer gates are affected
    unknown:
      meaning: evidence is insufficient; human/TL review required
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| seed が未解決 | `unknown` + `not_found` evidence |
| dependency edge に schema / contract / auth / CI / external tool boundary が含まれる | `broad` |
| affected gate が G8/G9/G12/G14 の deferred gate | `broad` + full-flow completion deny |
| impacted artifacts が allowed_files 外 | `interrupt` |
| impact graph のみ | improvement candidate。closure 不可 |
| external tool finding のみ | advisory evidence。closure 不可 |
| DB feedback snapshot のみ | candidate evidence。closure 不可 |
| 5 秒 SLA 超過 | partial result + `timeout=true`、空成功にしない |

## 6. Finding Vocabulary

governance hardening map へ渡す finding type は以下に固定する。現在フェーズでは L6 設計語彙であり、実 query CLI、DB 永続化、CI/equivalent enforcement ではない。

- `missing_dependency_edge`
- `unknown_scope`
- `affected_gate_missing`
- `feedback_ref_missing`

## 7. Output Contract

```yaml
impact_query_result:
  seed:
    kind: plan_id | artifact_path | symbol | schema_object | detector_finding
    value: string
  verdict: local | broad | unknown
  timeout: false
  affected:
    plans: []
    design_docs: []
    test_design_docs: []
    code_paths: []
    db_or_schema_objects: []
    gates: []
    feedback_refs: []
  dependency_edges:
    - source: string
      target: string
      relation: trace | dependency | generates | parent | blocks | evidence | tool_finding
      confidence: high | medium | low
  required_next:
    mode: add-feature | refactor | retrofit | incident | reverse | manual_review
    layer: L4 | L5 | L6 | L7 | L8 | L9 | L12 | L14
  completion:
    l6_design_closed: true
    l7_artifact_created_in_current_scope: false
    query_result_is_goal_completion: false
```

## 8. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| IMPACT-UT-CAND-01 | IMPACT-FN-01 | seed 種別を失わず正規化する |
| IMPACT-UT-CAND-02 | IMPACT-FN-02 | trace neighbor が空の場合に unknown を維持する |
| IMPACT-UT-CAND-03 | IMPACT-FN-03 | dependency edge が source / target / relation / confidence を持つ |
| IMPACT-UT-CAND-04 | IMPACT-FN-04 | schema / contract / deferred gate 影響を broad に分類する |
| IMPACT-UT-CAND-05 | IMPACT-FN-05 | PLAN / design / test-design / code / gate / feedback を分離して返す |
| IMPACT-UT-CAND-06 | IMPACT-FN-06 | feedback append は closure に昇格しない |
| IMPACT-UT-CAND-07 | IMPACT-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 9. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-IMPACT-01/unit-test-design.md` は現在タスクでは作成しない。
- `IMPACT-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- 実 query CLI、DB schema migration、CI/equivalent 接続、external tool execution は別 PLAN / 承認 / allowed_files / verification commands が必要である。
