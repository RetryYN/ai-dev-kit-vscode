---
doc_id: L6-FUNCTIONAL-DESIGN-FR-MIGR-01
title: Migration retrofit control 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-12
parent_requirements:
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/FR-EVT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - HELIX-workflows/helix-process/retrofit-workflow.md
artifact_type: design_doc
---

# Migration retrofit control 機能仕様

## 1. 目的

Migration retrofit control は、schema migration、retrofit、compatibility window、rollback、migration backlog の状態を管理し、破壊的変更を自動実行しないための機能である。

本仕様は L6 機能設計として、L3 `FR-MIGR-01`、L4 Runtime and Continuity、L5 persistence / migration 設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、schema migration、DB writer 変更、retrofit 実行は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-MIGR-01` | schema migration と retrofit の進行状況を管理する |
| `TR-05` | helix.db schema、view、migration log |
| `TR-08` | compatibility、deprecated warning、段階 retrofit |
| `FR-EVT-01` | migration / retrofit closure event を記録する |
| `FR-DOCTOR-01` | migration pending / compatibility warning を doctor summary に渡す |
| `DBEV-FN-*` | migration evidence lifecycle の状態を保持する |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| MIGR-FN-01 | `load_migration_plan(plan_id)` | migration / retrofit PLAN | migration plan | destructive 判定が無い plan を実行可能にしない |
| MIGR-FN-02 | `classify_migration_risk(plan)` | plan, schema diff, data operation | additive / compatible / destructive / unknown | unknown を additive に丸めない |
| MIGR-FN-03 | `validate_migration_approval(risk)` | risk, approval evidence | approval verdict | destructive は explicit human approval 必須 |
| MIGR-FN-04 | `build_migration_execution_window(plan)` | plan, compatibility window | execution / rollback window | rollback 不在で completed にしない |
| MIGR-FN-05 | `emit_migration_doctor_input(state)` | migration state | doctor input / detector finding | pending / blocked を summary に保持する |
| MIGR-FN-06 | `append_migration_feedback(state)` | state, evidence refs | events / metrics / feedback payload | append-only。feedback append は closure ではない |
| MIGR-FN-07 | `emit_migration_completion_guard_summary(state)` | state, strict full-flow status | goal audit summary | migration planned と full objective completion を分離する |

## 4. Migration Contract

```yaml
migration_control_summary:
  plan_id: string
  risk: additive | compatible | destructive | unknown
  state: planned | blocked | running | completed | rolled_back | deferred
  approval:
    required: bool
    approved: bool
    approval_ref: string
  compatibility:
    window_active: bool
    deprecated_routes: []
  rollback:
    available: bool
    command_ref: string
  completion:
    migration_plan_is_closure: false
    feedback_append_is_closure: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| destructive migration | `manual_approval_required`。自動実行不可 |
| risk unknown | `blocked` |
| rollback 不在 | completed 不可 |
| compatibility window 期限切れ | doctor warning / gate input |
| migration plan のみ | closure 不可 |
| feedback append のみ | closure 不可 |
| schema migration が必要 | current scope 外。別 PLAN / human confirmation 必須 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| MIGR-UT-CAND-01 | MIGR-FN-01 | destructive 判定なし plan を実行可能にしない |
| MIGR-UT-CAND-02 | MIGR-FN-02 | unknown を additive に丸めない |
| MIGR-UT-CAND-03 | MIGR-FN-03 | destructive は explicit human approval を要求する |
| MIGR-UT-CAND-04 | MIGR-FN-04 | rollback 不在で completed にしない |
| MIGR-UT-CAND-05 | MIGR-FN-05 | pending / blocked を doctor input に保持する |
| MIGR-UT-CAND-06 | MIGR-FN-06 | feedback append は closure に昇格しない |
| MIGR-UT-CAND-07 | MIGR-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-MIGR-01/unit-test-design.md` は現在タスクでは作成しない。
- `MIGR-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- schema migration、DB writer 変更、retrofit execution、rollback test、CI/equivalent 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
