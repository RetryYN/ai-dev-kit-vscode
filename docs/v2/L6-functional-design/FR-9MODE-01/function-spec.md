---
doc_id: L6-FUNCTIONAL-DESIGN-FR-9MODE-01
title: Nine-mode routing 機能仕様
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
  - docs/v2/L6-functional-design/FR-CTX-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-EVT-01/function-spec.md
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/cross-detection.md
artifact_type: design_doc
---

# Nine-mode routing 機能仕様

## 1. 目的

Nine-mode routing は、単一 signal または aggregate signal を受け取り、Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery の候補、priority、action、Forward return を返す機能である。

本仕様は L6 機能設計として、L3 `FR-9MODE-01`、L4 Entry and Routing、L5 内部処理設計、`workflow/detection-routing` の固定 map 原則を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、route CLI 実装、PLAN draft 自動生成は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-9MODE-01` | signal から mode 候補を選び、適切な workflow 入口を決める |
| `FR-CTX-01` | selected mode に必要な role / skill / command injection を返す |
| `FR-DRIFT-01` | drift signal / discrepancy signal の入力元 |
| `FR-EVT-01` | mode closure と Forward return event の接続先 |
| `workflow/detection-routing` | SIGNAL_TO_MODE 固定 map と 4 象限評価 |
| `workflow/cross-detection` | aggregate signal の入力元 |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| MODE9-FN-01 | `normalize_route_signal(signal)` | signal / aggregate signal / artifact evidence | normalized route signal | signal 不足を Forward 既定にしない |
| MODE9-FN-02 | `lookup_signal_to_mode(signal)` | normalized signal | mode / kind / subtype candidates | fixed map で mode を決め、4 象限で上書きしない |
| MODE9-FN-03 | `evaluate_route_priority(signal, impact)` | signal, uncertainty, impact | P0 / P1 / P2 / P3 + action | priority は mode と独立に決める |
| MODE9-FN-04 | `rank_route_candidates(candidates)` | candidates, priority | ordered candidates | 相反 signal は候補配列として返し、単一 pass にしない |
| MODE9-FN-05 | `attach_forward_return(candidate)` | candidate, affected layer | Forward return descriptor | V-model へ戻る layer を必ず持つ |
| MODE9-FN-06 | `append_route_feedback(candidate)` | route candidate, evidence refs | events / metrics / feedback payload | append-only。route candidate は closure ではない |
| MODE9-FN-07 | `emit_route_completion_guard_summary(state)` | route state, strict full-flow status | goal audit summary | route selected と full objective completion を分離する |

## 4. Routing Contract

```yaml
route_eval_result:
  signal_id: string
  signal: drift | debt_degradation | regression_prod | regression_dev | runaway | incident | unknown_design | aggregate
  candidates:
    - mode: Forward | Scrum | Discovery | Reverse | Incident | Add-feature | Refactor | Retrofit | Research | Recovery
      kind: string
      subtype: string
      priority: P0 | P1 | P2 | P3
      action: suggest_only | immediate_plan_draft | discovery_first | emergency_routing
      forward_return:
        layer: L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L12 | L14
        reason: string
  completion:
    route_candidate_is_closure: false
    plan_draft_is_closure: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| signal が SIGNAL_TO_MODE に未登録 | `manual_review_required` |
| signal 不足 | Forward 既定にせず `manual_review_required` |
| 4 象限評価の結果 | priority / action のみ更新。mode は変えない |
| P0 incident / runaway | human confirmation required |
| aggregate signal | cross-detection の evidence を保持して routing |
| PLAN draft 生成候補のみ | closure 不可 |
| strict full-flow deferred が残る | full objective completion deny |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| MODE9-UT-CAND-01 | MODE9-FN-01 | signal 不足を Forward 既定にしない |
| MODE9-UT-CAND-02 | MODE9-FN-02 | fixed map で mode を決める |
| MODE9-UT-CAND-03 | MODE9-FN-03 | 4 象限は priority / action のみ更新する |
| MODE9-UT-CAND-04 | MODE9-FN-04 | 相反 signal を候補配列として返す |
| MODE9-UT-CAND-05 | MODE9-FN-05 | Forward return layer を必ず持つ |
| MODE9-UT-CAND-06 | MODE9-FN-06 | feedback append は closure に昇格しない |
| MODE9-UT-CAND-07 | MODE9-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-9MODE-01/unit-test-design.md` は現在タスクでは作成しない。
- `MODE9-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- route CLI 実装、PLAN draft 自動生成、mode selection persistence、Forward return event writer は別 PLAN / 承認 / allowed_files / verification commands が必要である。
