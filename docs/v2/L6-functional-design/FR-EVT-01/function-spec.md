---
doc_id: L6-FUNCTIONAL-DESIGN-FR-EVT-01
title: Forward return event 機能仕様
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
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
upstream_design:
  - docs/v2/L4-basic-design/方式設計.md
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md
  - HELIX-workflows/helix-process/db-auto-registration.md
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/forward-return-discipline.md
  - HELIX-workflows/helix-process/plan-model.md
artifact_type: design_doc
---

# Forward return event 機能仕様

## 1. 目的

Forward return event は、Reverse / Discovery / Recovery / Incident / Add-feature / Refactor / Retrofit / Research / Scrum などの駆動 workflow が Forward V-model へ戻る時点で、戻し先 layer、触れた layer、再凍結 pair、closure metadata、DB feedback の接続情報を記録する機能である。

本仕様は L6 機能設計として、L3 `FR-EVT-01`、L4 Runtime and Continuity、`forward-return-discipline.md` の R1-R5、`db-auto-registration.md` のイベント駆動登録を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、mode closure DB schema、hook 実装、CI/equivalent 接続、外部ツール導入は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-07` / `FR-EVT-01` | 9 mode closure と Forward 復帰 event |
| `FR-PLAN-01` | Process / Action PLAN の `forward_return` と dependency / generates trace |
| `FR-IMPACT-01` | event を impact query の seed / dependency edge にする |
| `FR-INV-01` | event source の CLI / hook / PLAN / workflow doc を inventory に載せる |
| `DBEV-FN-*` | closure event を evidence lifecycle / feedback append へ渡す |
| `forward-return-discipline` | R1-R5、design_change_class、required_refreeze_pairs |
| `detection-routing` | DB 検出結果から workflow 起動、PLAN 起票、Forward 復帰へ戻す |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| EVT-FN-01 | `normalize_workflow_closure_event(raw_event)` | workflow close command / handover / hook / detector event | normalized closure event | source_workflow / target_forward_layer / source_event_id を失わない |
| EVT-FN-02 | `resolve_forward_return_contract(event, plan_record)` | closure event, Process / Action PLAN | forward_return contract | target_layer / touched_layers / design_change_class / required_refreeze_pairs を保持する |
| EVT-FN-03 | `validate_refreeze_requirements(contract, trace_state)` | forward_return contract, trace / VG-overview / requirement_drift | validation finding list | R1-R5 未充足を closure success にしない |
| EVT-FN-04 | `derive_closure_idempotency_key(event, contract)` | closure event, contract | idempotency key | 同一 workflow close を二重登録しない |
| EVT-FN-05 | `append_forward_return_evidence(event, validation)` | normalized event, validation finding | events / metrics / feedback payload | append-only。DB snapshot だけでは full closure 不可 |
| EVT-FN-06 | `route_unclosed_forward_return(validation)` | validation finding | route / PLAN / PR candidate | missing pair / unknown design_change_class を既存 workflow へ戻す |
| EVT-FN-07 | `emit_event_guard_summary(event, validation)` | event, strict full-flow status | goal audit summary | L6設計閉塞と L7/右腕 gate closure を分離する |

## 4. Event State Machine

```yaml
forward_return_event_state:
  states:
    - closure_requested
    - event_normalized
    - forward_return_resolved
    - refreeze_validated
    - evidence_appended
    - route_candidate_generated
    - closure_denied_or_ready
  terminal_verdict:
    ready:
      meaning: required_refreeze_pairs have evidence and no blocking finding remains
    denied:
      meaning: pair freeze, trace, design_change_class, or layer contract is missing
    candidate:
      meaning: route / PLAN / PR candidate generated, but not adopted yet
```

## 5. Output Contract

```yaml
forward_return_event:
  source_workflow: reverse | discovery | recovery | incident | add-feature | refactor | retrofit | research | scrum | forward
  source_event_id: string
  source_plan_id: string
  parent_process: string
  target_forward_layer: L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | L14
  touched_layers: []
  design_change_class: pure_impl | design_or_contract_changed | unknown
  required_refreeze_pairs:
    - L6-L7
    - L5-L8
    - L4-L9
  refreeze_evidence:
    machine_clean: bool
    semantic_pass: bool
    evidence_refs: []
  idempotency_key: string
  feedback:
    append_only: true
    candidate_generated: bool
    closure_allowed: false
```

## 6. 判定ルール

| Rule | 判定 |
|---|---|
| `source_workflow` 欠落 | `missing_source_workflow` |
| `target_forward_layer` 欠落 | `missing_target_forward_layer` |
| `design_change_class=unknown` | `refreeze_required` |
| touched layer が L7/L8/L9 なのに pair が空 | `missing_required_refreeze_pair` |
| R1-R5 の machine-clean 不足 | `forward_return_denied` |
| semantic gate 未記録 | `semantic_gate_required` |
| idempotency key 衝突 | duplicate として append せず既存 event を参照 |
| DB event append のみ | candidate evidence。closure 不可 |
| route / PLAN / PR candidate のみ | 採用前。closure 不可 |
| strict full-flow deferred が残る | full objective completion deny |

## 7. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| EVT-UT-CAND-01 | EVT-FN-01 | source_workflow / target_forward_layer を失わず正規化する |
| EVT-UT-CAND-02 | EVT-FN-02 | forward_return contract の required fields 欠落を finding にする |
| EVT-UT-CAND-03 | EVT-FN-03 | R1-R5 未充足を closure success にしない |
| EVT-UT-CAND-04 | EVT-FN-04 | idempotency key が同一 close の二重登録を防ぐ |
| EVT-UT-CAND-05 | EVT-FN-05 | evidence append を full closure に昇格しない |
| EVT-UT-CAND-06 | EVT-FN-06 | missing pair / unknown design_change_class を route candidate にする |
| EVT-UT-CAND-07 | EVT-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 8. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-EVT-01/unit-test-design.md` は現在タスクでは作成しない。
- `EVT-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- mode closure DB schema、hook 実装、event writer 実装、CI/equivalent 接続、right-arm execution gate closure は別 PLAN / 承認 / allowed_files / verification commands が必要である。
