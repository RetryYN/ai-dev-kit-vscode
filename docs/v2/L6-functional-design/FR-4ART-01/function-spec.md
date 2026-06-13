---
doc_id: L6-FUNCTIONAL-DESIGN-FR-4ART-01
title: Four artifact trace audit 機能仕様
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
  - docs/v2/L6-functional-design/FR-TDD-01/function-spec.md
  - docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md
  - docs/v2/L6-functional-design/whole-source-coverage-機能設計.md
artifact_type: design_doc
---

# Four artifact trace audit 機能仕様

## 1. 目的

Four artifact trace audit は、設計、実装、テスト設計、テストコードの 4 artifact が同じ機能単位で追跡できるかを監査し、片肺、孤児 artifact、wrong-layer pair、coverage claim の過大評価を検出する機能である。

本仕様は L6 機能設計として、L3 `FR-4ART-01`、L4 Plan and Gate Control、L5 内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、trace auditor 実装、G7 / strict full-flow gate 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-4ART-01` | 設計、実装、テスト設計、テストコードの trace 欠落を監査する |
| `FR-TDD-01` | test-first / implementation order の証跡を参照する |
| `FR-PLAN-01` | PLAN dependency / generates / allowed_files を参照する |
| `FR-GATE-01` | trace 欠落を gate verdict input にする |
| `FR-DRIFT-01` | 片肺や orphan を drift route に渡す |
| `whole-source-coverage` | 既存実装由来の FN-WSC / UT-WSC trace を参考にする |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| ART4-FN-01 | `collect_four_artifact_refs(feature_id)` | feature / PLAN / doc / code seed | design / implementation / test_design / test_code refs | 存在しない artifact を生成済みにしない |
| ART4-FN-02 | `normalize_pair_keys(refs)` | refs | normalized feature keys | FR ID / FN ID / UT ID の対応を壊さない |
| ART4-FN-03 | `evaluate_trace_completeness(keys)` | normalized keys | missing / orphan / wrong_layer / complete findings | orphan を coverage に含めない |
| ART4-FN-04 | `evaluate_balance_ratio(findings)` | findings | balance ratio / coverage pct | coverage 100 と balance 1.0 を別値として保持する |
| ART4-FN-05 | `emit_artifact_trace_gate_input(summary)` | summary | gate input / detector finding | required pair 欠落を pass にしない |
| ART4-FN-06 | `append_artifact_trace_feedback(summary)` | summary, evidence refs | events / metrics / feedback payload | append-only。feedback append は closure ではない |
| ART4-FN-07 | `emit_artifact_completion_guard_summary(summary)` | summary, strict full-flow status | goal audit summary | L6 focus clean と full objective completion を分離する |

## 4. Trace Contract

```yaml
four_artifact_trace_summary:
  feature_id: string
  artifacts:
    design: []
    implementation: []
    test_design: []
    test_code: []
  findings:
    missing_pair: []
    orphan_artifact: []
    wrong_layer_pair: []
    semantic_excluded_orphan: []
  metrics:
    coverage_pct: number
    balance_ratio: number
  gate_input:
    blocking: bool
    advisory: bool
  completion:
    four_artifact_trace_is_goal_completion: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| L6 design に対応する test_design が存在しない | `missing_pair` |
| test_design が上位 design に戻れない | `orphan_artifact` |
| L6 design が L8 / L9 / L12 / L14 test design と直接 pair している | `wrong_layer_pair` |
| semantic exclusion の owner / reason / source が欠落 | waiver 不成立 |
| coverage 100 でも balance_ratio < 1.0 | full-flow completion deny |
| candidate / PLAN materialized のみ | closure 不可 |
| current scope で L7 artifact 作成が必要 | add-feature 起票へ戻す |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| ART4-UT-CAND-01 | ART4-FN-01 | 4 artifact ref を種別別に分離する |
| ART4-UT-CAND-02 | ART4-FN-02 | FR / FN / UT key を対応付ける |
| ART4-UT-CAND-03 | ART4-FN-03 | missing / orphan / wrong_layer を分離する |
| ART4-UT-CAND-04 | ART4-FN-04 | coverage と balance_ratio を混同しない |
| ART4-UT-CAND-05 | ART4-FN-05 | required pair 欠落を gate input に保持する |
| ART4-UT-CAND-06 | ART4-FN-06 | feedback append は closure に昇格しない |
| ART4-UT-CAND-07 | ART4-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-4ART-01/unit-test-design.md` は現在タスクでは作成しない。
- `ART4-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- trace auditor 実装、G7 / G8 / G9 / G12 / G14 gate 接続、CI/equivalent 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
