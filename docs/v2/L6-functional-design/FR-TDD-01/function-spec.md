---
doc_id: L6-FUNCTIONAL-DESIGN-FR-TDD-01
title: TDD順序強制 機能仕様
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
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md
  - docs/v2/L6-functional-design/coding-rule-detector-機能設計.md
  - docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
artifact_type: design_doc
---

# TDD順序強制 機能仕様

## 1. 目的

FR-TDD-01 は、実装作業が「テスト設計 / テスト実装 / failing 確認 / 最小実装 / review / 強化 test / 修正」の順序を破って進むことを防ぐ機能である。

本仕様は L6 機能設計として、既存 L1/L3/L4 の TDD 順序強制要件を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、実装、CI 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-03` / `FR-TDD-01` | TDD 順序 fail-close 要件 |
| `FR-PLAN-01` | PLAN dependency / generates / allowed_files を順序判定に渡す |
| `FR-GATE-01` | gate 判定に TDD 順序違反を入力する |
| `FR-4ART-01` | 設計、テスト設計、実装、テストコードの trace を照合する |
| `DBEV-FN-*` | 順序違反、candidate、verification evidence を HELIX DB feedback へ append する |
| `HEXT-FN-*` | 外部ツール findings を TDD 違反の advisory evidence として扱う |

## 3. Function Contract

| FN-ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| TDD-FN-01 | `load_tdd_order_contract(plan_id, repo_root)` | PLAN / task-plan / handover / phase evidence | `TddOrderContract` | 必須 step 定義が無ければ `blocked` を返し、暗黙許可しない |
| TDD-FN-02 | `collect_tdd_evidence(contract)` | test design path, test file path, command result, review evidence | `TddEvidenceSet` | evidence は read-only 収集。存在しない証跡を生成済みにしない |
| TDD-FN-03 | `evaluate_step_transition(contract, evidence, requested_step)` | 現状態、要求 step、証跡 | `allow / block / interrupt` | S2 不在の S3、S5 不在の S7、failing 確認なしの本体実装を block |
| TDD-FN-04 | `emit_tdd_guard_finding(verdict)` | transition verdict | detector finding / gate input | P0/P1 は gate 入力、P2/P3 は advisory。severity を黙殺しない |
| TDD-FN-05 | `append_tdd_feedback(verdict, evidence_refs)` | verdict, evidence refs | events / metrics / feedback payload | append-only。DB snapshot だけでは closure 不可 |
| TDD-FN-06 | `build_tdd_impact_edges(verdict)` | affected PLAN / artifact / function IDs | dependency / impact graph edges | source -> affected artifact -> required gate を返す |
| TDD-FN-07 | `emit_tdd_completion_guard_summary(state)` | guard state, strict full-flow status | goal audit summary | L6 focus clean と full-flow completion を混同しない |

## 4. State Machine

```yaml
tdd_order_state:
  allowed_sequence:
    - S1_PLAN_ready
    - S2_test_design_or_test_stub_ready
    - S3_failing_test_observed
    - S4_minimal_implementation
    - S5_review_and_additional_tests
    - S6_test_execution_passed
    - S7_fix_and_closure
  forbidden_transitions:
    - from: S1_PLAN_ready
      to: S4_minimal_implementation
      reason: test_after_implementation
    - from: S2_test_design_or_test_stub_ready
      to: S7_fix_and_closure
      reason: missing_execution_evidence
    - from: S5_review_and_additional_tests
      to: goal_complete
      reason: missing_gate_or_ci_equivalent
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| PLAN / handover に allowed_files が無い | `blocked` |
| requested_step が Next Action / WBS 外 | `interrupt` |
| テスト設計またはテスト stub なしで実装 step | `blocked` |
| failing 確認なしで本体実装完了 claim | `blocked` |
| test pass なしで closure claim | `blocked` |
| CI/equivalent なしの full-flow completion claim | `blocked` |
| external tool finding のみ | advisory evidence。closure 不可 |
| DB feedback snapshot のみ | candidate evidence。closure 不可 |

## 6. Finding Vocabulary

governance hardening map へ渡す finding type は以下に固定する。現在フェーズでは L6 設計語彙であり、L7 実装、単体テスト実行、fail-close 昇格ではない。

- `missing_test_design_or_stub`
- `missing_failing_test_observation`
- `implementation_before_test`
- `closure_without_test_pass`

## 7. Output Contract

```yaml
tdd_guard_summary:
  plan_id: string
  requested_step: string
  verdict: allow | block | interrupt
  reason: string
  required_evidence:
    - test_design_or_stub
    - failing_test_observed
    - passing_test_result
    - review_or_gate_result
  evidence_refs: []
  impact_edges: []
  feedback:
    append_only: true
    candidate_generated: bool
    closure_allowed: false
  completion:
    l6_design_closed: true
    l7_artifact_created_in_current_scope: false
    full_goal_completion_allowed: false
```

## 8. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 FN | 期待 |
|---|---|---|
| TDD-UT-CAND-01 | TDD-FN-01 | step contract 欠落時に暗黙 allow しない |
| TDD-UT-CAND-02 | TDD-FN-03 | S2 不在の S3 / S4 を block |
| TDD-UT-CAND-03 | TDD-FN-03 | failing test 未観測の implementation claim を block |
| TDD-UT-CAND-04 | TDD-FN-04 | severity P0/P1 を gate input へ保持 |
| TDD-UT-CAND-05 | TDD-FN-05 | feedback append は closure に昇格しない |
| TDD-UT-CAND-06 | TDD-FN-06 | impact edges が source -> artifact -> gate の形を保つ |
| TDD-UT-CAND-07 | TDD-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 9. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-TDD-01/unit-test-design.md` は現在タスクでは作成しない。
- `TDD-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- CI/equivalent 接続、gate fail-close 昇格、実装コード、外部ツール実行は別 PLAN / 承認 / allowed_files / verification commands が必要である。
