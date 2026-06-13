---
doc_id: L6-FUNCTIONAL-DESIGN-FR-GR-01
title: Guardrail fail-close 機能仕様
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
  - docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md
  - docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
artifact_type: design_doc
---

# Guardrail fail-close 機能仕様

## 1. 目的

Guardrail fail-close は、Coverage、Agent Error Budget、TTFSP、scope boundary、external-tool approval、Codex / Claude parity の逸脱を監視し、`pass / warn / block / throttle` を返す機能である。

本仕様は L6 機能設計として、L3 `FR-GR-01`、L4 Audit and Quality、L5 内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、guardrail 実装、hook / doctor / gate / CI 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-GR-01` | guardrail 条件を監視し、危険な実行を block または throttle する |
| `FR-GATE-01` | guardrail verdict を gate input にする |
| `FR-DOCTOR-01` | guardrail 集約 summary を doctor へ渡す |
| `FR-CHANGEPROP-01` | regression / ratchet 違反を guardrail input にする |
| `TR-02` | model routing と role-based injection を guardrail 対象にする |
| `DBEV-FN-*` | guardrail event / feedback を append-only で記録する |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| GR-FN-01 | `load_guardrail_policy(scope)` | layer, role, PLAN, handover, runtime | guardrail policy | policy 欠落を暗黙 pass にしない |
| GR-FN-02 | `collect_guardrail_metrics(policy)` | coverage, error budget, TTFSP, scope, approval evidence | metric set | 計測ソース不在を成功扱いにしない |
| GR-FN-03 | `evaluate_guardrail_axis(metrics)` | metric set | axis verdict list | 各 axis を独立評価し、他 axis の pass で相殺しない |
| GR-FN-04 | `merge_guardrail_verdict(axis_verdicts)` | axis verdict list | pass / warn / block / throttle | block > throttle > warn > pass の優先順位を守る |
| GR-FN-05 | `emit_guardrail_gate_input(verdict)` | verdict | gate input / detector finding | block を advisory に降格しない |
| GR-FN-06 | `append_guardrail_feedback(verdict)` | verdict, evidence refs | events / metrics / feedback payload | append-only。feedback append は closure ではない |
| GR-FN-07 | `emit_guardrail_completion_guard_summary(state)` | guard state, strict full-flow status | goal audit summary | L6 design closure と full objective completion を分離する |

## 4. Guardrail Contract

```yaml
guardrail_verdict:
  scope:
    layer: string
    role: string
    plan_id: string
    handover_owner: string
  axes:
    coverage:
      verdict: pass | warn | block
      threshold: number
    error_budget:
      verdict: pass | warn | block | throttle
      threshold: number
    ttfsp:
      verdict: pass | warn | throttle
      threshold_minutes: number
    scope_boundary:
      verdict: pass | block
    external_tool_approval:
      verdict: pass | block
    codex_claude_parity:
      verdict: pass | warn | block
  final_verdict: pass | warn | block | throttle
  completion:
    feedback_append_is_closure: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| guardrail policy 欠落 | `block` |
| current scope 外ファイル変更が必要 | `block` + human confirmation |
| external tool install / auth / env / CI 変更が未承認 | `block` |
| Codex では効かず ClaudeCode だけ効く guard | `warn` または `block`。差分を parity finding にする |
| critical guardrail 1 件以上 | gate fail input |
| warning のみ | `warn`。closure 不可 |
| feedback append のみ | closure 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| GR-UT-CAND-01 | GR-FN-01 | policy 欠落を暗黙 pass にしない |
| GR-UT-CAND-02 | GR-FN-02 | 計測ソース不在を warning / block に保持する |
| GR-UT-CAND-03 | GR-FN-03 | axis verdict を独立評価する |
| GR-UT-CAND-04 | GR-FN-04 | block > throttle > warn > pass の優先順位を守る |
| GR-UT-CAND-05 | GR-FN-05 | block を gate input に保持する |
| GR-UT-CAND-06 | GR-FN-06 | feedback append は closure に昇格しない |
| GR-UT-CAND-07 | GR-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-GR-01/unit-test-design.md` は現在タスクでは作成しない。
- `GR-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- guardrail 実装、hook / doctor / gate / CI 接続、external tool approval enforcement は別 PLAN / 承認 / allowed_files / verification commands が必要である。
