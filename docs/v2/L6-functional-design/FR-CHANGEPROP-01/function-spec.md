---
doc_id: L6-FUNCTIONAL-DESIGN-FR-CHANGEPROP-01
title: Change propagation ratchet 機能仕様
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
  - docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
artifact_type: design_doc
---

# Change propagation ratchet 機能仕様

## 1. 目的

Change propagation ratchet は、上流変更に対して下流の設計、テスト設計、実装、検証、feedback が追従しているかを監査し、trace / balance / gate 状態の後戻りを禁止する機能である。

本仕様は L6 機能設計として、L3 `FR-CHANGEPROP-01`、L4 Audit and Quality、L5 内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、ratchet 実装、DB history table、doctor / push / CI 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-CHANGEPROP-01` | 上流変更に対する下流追従と balance_ratio の後戻り禁止を監査する |
| `FR-IMPACT-01` | 変更 seed から affected graph を返す |
| `FR-PLAN-01` | PLAN dependency / generates の追従状態を確認する |
| `FR-DOCTOR-01` | 複数監査結果の summary に ratchet 結果を渡す |
| `FR-GATE-01` | 後戻りを gate verdict input にする |
| `DBEV-FN-*` | baseline / after snapshot / recurrence closure を feedback loop に載せる |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| CHPROP-FN-01 | `capture_change_baseline(scope)` | before state, trace metrics, gate summary | baseline snapshot | baseline なしで改善 claim を許可しない |
| CHPROP-FN-02 | `resolve_downstream_obligations(change)` | changed requirements / design / PLAN / code | required downstream updates | affected layer / pair / gate を失わない |
| CHPROP-FN-03 | `evaluate_propagation_completion(obligations, after)` | obligations, after state | complete / partial / missing | missing を complete にしない |
| CHPROP-FN-04 | `evaluate_ratchet_regression(baseline, after)` | baseline, after metrics | regression findings | coverage / balance / blocking count の悪化を見逃さない |
| CHPROP-FN-05 | `emit_changeprop_gate_input(findings)` | propagation + ratchet findings | gate input / detector finding | regression を advisory に降格しない |
| CHPROP-FN-06 | `append_changeprop_feedback(findings)` | findings, evidence refs | events / metrics / feedback payload | append-only。snapshot だけでは closure 不可 |
| CHPROP-FN-07 | `emit_changeprop_completion_guard_summary(state)` | state, strict full-flow status | goal audit summary | local improvement と full objective completion を分離する |

## 4. Propagation Contract

```yaml
change_propagation_summary:
  change_id: string
  source_artifacts: []
  baseline:
    trace_coverage: number
    balance_ratio: number
    blocking_findings: number
  obligations:
    design_docs: []
    test_design_docs: []
    code_paths: []
    test_paths: []
    gates: []
    feedback_records: []
  propagation_status: complete | partial | missing
  ratchet:
    regression_detected: bool
    worsened_metrics: []
  completion:
    baseline_snapshot_is_closure: false
    feedback_append_is_closure: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| baseline が無い改善 claim | `blocked` |
| affected downstream artifact が未更新 | `partial` or `missing` |
| coverage / balance_ratio が baseline より悪化 | `regression_detected=true` |
| blocking findings が増加 | gate fail input |
| downstream obligation が allowed_files 外 | `interrupt` |
| feedback append のみ | closure 不可 |
| strict full-flow deferred が残る | full objective completion deny |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| CHPROP-UT-CAND-01 | CHPROP-FN-01 | baseline なしの改善 claim を許可しない |
| CHPROP-UT-CAND-02 | CHPROP-FN-02 | affected layer / pair / gate を obligations に保持する |
| CHPROP-UT-CAND-03 | CHPROP-FN-03 | downstream 未追従を complete にしない |
| CHPROP-UT-CAND-04 | CHPROP-FN-04 | coverage / balance / blocking count の悪化を検出する |
| CHPROP-UT-CAND-05 | CHPROP-FN-05 | regression を gate input に保持する |
| CHPROP-UT-CAND-06 | CHPROP-FN-06 | feedback append は closure に昇格しない |
| CHPROP-UT-CAND-07 | CHPROP-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-CHANGEPROP-01/unit-test-design.md` は現在タスクでは作成しない。
- `CHPROP-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- ratchet 実装、DB history table、doctor / push / CI 接続、recurrence closure は別 PLAN / 承認 / allowed_files / verification commands が必要である。
