---
doc_id: L6-FUNCTIONAL-DESIGN-FR-DRIFT-01
title: Drift routing 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-12
parent_requirements:
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-EVT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/cross-detection.md
artifact_type: design_doc
---

# Drift routing 機能仕様

## 1. 目的

Drift routing は、要件、設計、PLAN、実装証跡、テスト証跡、外部 tool finding、運用 feedback の差分を分類し、interrupt / recovery / reverse / refactor / incident / add-feature / manual_review のどこへ戻すかを決める機能である。

本仕様は L6 機能設計として、L3 `FR-DRIFT-01`、L4 Entry and Routing、L5 内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、routing 実装、hook / doctor / gate 接続、HELIX DB writer 変更は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-DRIFT-01` | drift を分類し、interrupt / recovery / reverse などへ振り分ける |
| `FR-9MODE-01` | signal から mode 候補を選ぶ |
| `FR-IMPACT-01` | drift seed から影響範囲を返す |
| `FR-EVT-01` | routing 判定と Forward return event を接続する |
| `FR-GATE-01` | blocking / advisory を gate verdict input にする |
| `DBEV-FN-*` | drift finding を candidate / adoption / recurrence closure に載せる |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| DRIFT-FN-01 | `normalize_drift_signal(signal)` | doctor finding, hook event, feedback item, external tool finding | normalized drift signal | source / severity / layer / evidence_ref を失わない |
| DRIFT-FN-02 | `classify_drift_type(signal)` | normalized signal | requirement / design / trace / test / runtime / tool / feedback drift | unknown を pass にしない |
| DRIFT-FN-03 | `rank_drift_severity(signal, impact)` | signal, impact query result | P0 / P1 / P2 / P3 | auth / schema / strict-full-flow / data loss 影響を低 severity にしない |
| DRIFT-FN-04 | `select_recovery_route(classification)` | drift type, severity, layer, scope | route decision | Forward return layer を必ず保持する |
| DRIFT-FN-05 | `emit_drift_gate_input(route)` | route decision | gate input / detector finding | blocking drift を advisory に降格しない |
| DRIFT-FN-06 | `append_drift_feedback(route)` | route decision, evidence refs | events / metrics / feedback payload | append-only。candidate_generated は closure ではない |
| DRIFT-FN-07 | `emit_drift_completion_guard_summary(state)` | drift state, strict full-flow status | goal audit summary | L6 design closure と full objective completion を分離する |

## 4. Routing Contract

```yaml
drift_route_decision:
  signal_id: string
  source: doctor | hook | review | feedback | external_tool | manual
  drift_type: requirement | design | trace | test | runtime | tool | feedback | unknown
  severity: P0 | P1 | P2 | P3
  affected_layers: []
  forward_return:
    layer: L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L12 | L14
    reason: string
  route: interrupt | recovery | reverse | refactor | incident | add-feature | manual_review
  gate_input:
    blocking: bool
    advisory: bool
  completion:
    route_candidate_is_closure: false
    feedback_append_is_closure: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| 上位要件に戻れない L4-L6 artifact | `requirement` drift + `reverse` or `interrupt` |
| L6 仕様に対応する test-design / code / test-code trace 欠落 | `trace` drift + `add-feature` or `recovery` |
| strict full-flow deferred が残る完了 claim | `test` drift + gate fail |
| 外部 tool finding だけ | advisory。PLAN / gate 採用前は closure 不可 |
| feedback candidate だけ | candidate。PLAN / PR / gate evidence 前は closure 不可 |
| impacted scope が allowed_files 外 | `interrupt` |
| source が不明 | `manual_review`。pass 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| DRIFT-UT-CAND-01 | DRIFT-FN-01 | signal の source / severity / evidence_ref を保持する |
| DRIFT-UT-CAND-02 | DRIFT-FN-02 | unknown drift を pass にしない |
| DRIFT-UT-CAND-03 | DRIFT-FN-03 | strict-full-flow / schema / auth 影響を低 severity にしない |
| DRIFT-UT-CAND-04 | DRIFT-FN-04 | route decision が Forward return layer を持つ |
| DRIFT-UT-CAND-05 | DRIFT-FN-05 | blocking drift を advisory に降格しない |
| DRIFT-UT-CAND-06 | DRIFT-FN-06 | feedback append は closure に昇格しない |
| DRIFT-UT-CAND-07 | DRIFT-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-DRIFT-01/unit-test-design.md` は現在タスクでは作成しない。
- `DRIFT-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- routing 実装、doctor / gate 接続、hook 接続、HELIX DB writer、feedback recurrence closure は別 PLAN / 承認 / allowed_files / verification commands が必要である。
