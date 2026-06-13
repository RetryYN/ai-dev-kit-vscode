---
doc_id: L6-FUNCTIONAL-DESIGN-FR-NSM-01
title: NSM alignment score 機能仕様
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
  - docs/v2/L6-functional-design/FR-EVT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
artifact_type: design_doc
---

# NSM alignment score 機能仕様

## 1. 目的

NSM alignment score は、PLAN 完遂、pair freeze、4 artifact trace、gate pass、feedback recurrence closure を集計し、週次 / 月次の HELIX 整合スコアと公開可否を返す機能である。

本仕様は L6 機能設計として、L3 `FR-NSM-01`、L4 Runtime and Continuity、L5 内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、score view 実装、dashboard / DB view / scheduler 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-NSM-01` | PLAN 完遂状況と整合スコアを集計し、運用判断の基礎指標を提供する |
| `FR-EVT-01` | event / mode closure を score input にする |
| `FR-DOCTOR-01` | doctor summary を score input にする |
| `FR-GATE-01` | gate pass / approved_deferred を score input にする |
| `DBEV-FN-*` | evidence lifecycle の状態を score input にする |
| `observability-sre` | SLI / SLO / error budget の運用判断観点 |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| NSM-FN-01 | `collect_alignment_inputs(period)` | plan_registry, gate runs, trace summary, feedback records | alignment input set | 必須 input 欠落をゼロ点成功にしない |
| NSM-FN-02 | `evaluate_six_axes(inputs)` | input set | layer / kind / pair_freeze / 4artifact / gate_pass / done axis results | axis ごとの根拠を保持する |
| NSM-FN-03 | `calculate_alignment_score(axis_results)` | axis results | score / confidence | confidence 低を高 score で隠さない |
| NSM-FN-04 | `decide_score_publishability(score)` | score, missing inputs, strict full-flow | pending / computed / published / deferred | trace 欠落時は published にしない |
| NSM-FN-05 | `emit_nsm_doctor_input(summary)` | summary | doctor input / detector finding | score 低下を advisory に固定しない |
| NSM-FN-06 | `append_nsm_feedback(summary)` | summary, evidence refs | events / metrics / feedback payload | append-only。score publish は closure ではない |
| NSM-FN-07 | `emit_nsm_completion_guard_summary(state)` | state, strict full-flow status | goal audit summary | NSM computed と full objective completion を分離する |

## 4. Score Contract

```yaml
nsm_alignment_score:
  period:
    from: date
    to: date
  axes:
    layer: pass | warn | fail | missing
    kind: pass | warn | fail | missing
    pair_freeze: pass | warn | fail | missing
    four_artifact: pass | warn | fail | missing
    gate_pass: pass | warn | fail | missing
    done: pass | warn | fail | missing
  score:
    value: number
    confidence: high | medium | low
  status: pending | computed | published | deferred
  completion:
    score_published_is_goal_completion: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| 必須 input 欠落 | `pending` または `deferred`。published 不可 |
| strict full-flow deferred が残る | full objective completion deny |
| gate approved_deferred を pass と混同 | fail |
| confidence low | published 不可 |
| feedback append のみ | closure 不可 |
| score computed のみ | closure 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| NSM-UT-CAND-01 | NSM-FN-01 | 必須 input 欠落をゼロ点成功にしない |
| NSM-UT-CAND-02 | NSM-FN-02 | 6 axes ごとの根拠を保持する |
| NSM-UT-CAND-03 | NSM-FN-03 | confidence 低を高 score で隠さない |
| NSM-UT-CAND-04 | NSM-FN-04 | trace 欠落時に published にしない |
| NSM-UT-CAND-05 | NSM-FN-05 | score 低下を doctor input に保持する |
| NSM-UT-CAND-06 | NSM-FN-06 | feedback append は closure に昇格しない |
| NSM-UT-CAND-07 | NSM-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-NSM-01/unit-test-design.md` は現在タスクでは作成しない。
- `NSM-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- score view 実装、dashboard / scheduler / DB view 接続、運用 SLO 連携は別 PLAN / 承認 / allowed_files / verification commands が必要である。
