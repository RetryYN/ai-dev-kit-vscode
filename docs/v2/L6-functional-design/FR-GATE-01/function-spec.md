---
doc_id: L6-FUNCTIONAL-DESIGN-FR-GATE-01
title: Gate verdict synthesis 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
parent_requirements:
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/FR-TDD-01/function-spec.md
  - docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md
  - docs/v2/L6-functional-design/FR-EVT-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - HELIX-workflows/helix-process/forward-return-discipline.md
artifact_type: design_doc
---

# Gate verdict synthesis 機能仕様

## 1. 目的

Gate verdict synthesis は、定量 detector 結果、定性 review 結果、V-model pair 状態、PLAN / handover scope、waiver、strict full-flow 状態を合成し、`pass / warn / fail / approved_deferred / not_applicable` を一貫して返す機能である。

本仕様は L6 機能設計として、L3 `FR-GATE-01`、L4 Plan and Gate Control、`automation-gate-map.md`、`forward-return-discipline.md` の R1-R5 を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、gate body 実装、doctor / push / CI 接続変更、右腕 execution gate 実装は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-GATE-01` | static check と AI review 条件を束ね gate verdict を返す |
| `FR-TDD-01` | テストアフター、TDD順序違反を gate input にする |
| `FR-PLAN-01` | PLAN dependency / allowed_files / generates trace を gate input にする |
| `FR-4ART-01` | 4 artifact / pair freeze の trace 状態を gate input にする |
| `FR-EVT-01` | gate verdict と Forward return event を DB feedback へ接続する |
| `DBEV-FN-*` | verdict evidence を adoption lifecycle に載せる |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| GATE-FN-01 | `collect_gate_inputs(gate_id, scope)` | gate id, PLAN / handover / pair / detector refs | normalized gate input | evidence source と scope boundary を失わない |
| GATE-FN-02 | `evaluate_quantitative_checks(inputs)` | detector / command / trace / coverage result | quantitative verdict list | blocking detector を warn に降格しない |
| GATE-FN-03 | `evaluate_qualitative_checks(inputs)` | review / semantic gate / TL-PM decision | qualitative verdict list | semantic gate 未実施を pass にしない |
| GATE-FN-04 | `merge_gate_verdicts(quant, qual, waiver)` | quantitative, qualitative, waiver | final verdict | fail > approved_deferred > warn > pass の優先順位を守る |
| GATE-FN-05 | `separate_candidate_from_closure(verdict, evidence)` | verdict, candidate / PLAN / PR / DB evidence | closure boundary | candidate_generated / plan_materialized を pass と混同しない |
| GATE-FN-06 | `emit_gate_feedback(verdict)` | final verdict | events / metrics / feedback payload | append-only。feedback append だけでは closure 不可 |
| GATE-FN-07 | `emit_gate_guard_summary(verdict, strict_full_flow)` | verdict, strict full-flow status | goal audit summary | L6 focus clean と full objective completion を分離する |

## 4. Verdict Contract

```yaml
gate_verdict:
  gate_id: string
  pair: L6-L7 | L5-L8 | L4-L9 | L3-L12 | L2-L10 | L1-L14
  scope:
    current_scope_sufficient: bool
    allowed_files: []
    out_of_scope: []
  quantitative:
    blocking: []
    warning: []
    pass: []
  qualitative:
    semantic_gate_required: bool
    semantic_gate_passed: bool
    review_refs: []
  waiver:
    applicable: bool
    reason: string
    owner: string
    unskip_required_when: []
  verdict: pass | warn | fail | approved_deferred | not_applicable
  closure:
    candidate_generated_is_closure: false
    plan_materialized_is_closure: false
    db_snapshot_is_closure: false
    gate_passed: bool
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| blocking detector が 1 件以上 | `fail` |
| 必須 artifact 不在 | `fail` |
| semantic gate required かつ未実施 | `approved_deferred` または `fail`。scope / policy で決めるが pass 不可 |
| execution gate 未実装かつ current scope 外 | `approved_deferred` |
| UI なしなど明示 waiver が完全 | `not_applicable` |
| waiver の owner / reason / unskip 条件欠落 | waiver 不成立、`fail` または `warn` |
| candidate_generated のみ | `approved_deferred` または `warn`。pass 不可 |
| PLAN materialized のみ | pass 不可 |
| DB snapshot / feedback append のみ | pass 不可 |
| strict full-flow deferred が残る | full objective completion deny |

## 6. 定量 / 定性 Double Check

| 入力 | 分類 | 例 | closure への寄与 |
|---|---|---|---|
| detector / doctor / trace / coverage | quantitative | requirement_drift clean、trace coverage 100、G7 anchored 88/88 | 必要条件 |
| semantic gate / TL review / PM approval | qualitative | L4-L9 semantic excluded orphan 判断、scope expansion approval | 十分条件の一部 |
| PLAN / PR / DB candidate | candidate evidence | feedback-loop plan_candidates / pr_candidates | closure 不可 |
| gate pass / CI equivalent / recurrence closure | closure evidence | strict full-flow clean、CI/equivalent run、feedback_closed | full goal completion の条件 |

## 7. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| GATE-UT-CAND-01 | GATE-FN-01 | gate input が source と scope boundary を保持する |
| GATE-UT-CAND-02 | GATE-FN-02 | blocking detector を warn / pass に降格しない |
| GATE-UT-CAND-03 | GATE-FN-03 | semantic gate 未実施を pass にしない |
| GATE-UT-CAND-04 | GATE-FN-04 | fail > approved_deferred > warn > pass の優先順位を守る |
| GATE-UT-CAND-05 | GATE-FN-05 | candidate / PLAN / DB snapshot を closure と混同しない |
| GATE-UT-CAND-06 | GATE-FN-06 | gate feedback append を closure に昇格しない |
| GATE-UT-CAND-07 | GATE-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 8. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-GATE-01/unit-test-design.md` は現在タスクでは作成しない。
- `GATE-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- gate body 実装、doctor / push / CI 接続変更、G8/G9/G12/G14 execution gate 実装、feedback_closed 証跡化は別 PLAN / 承認 / allowed_files / verification commands が必要である。
