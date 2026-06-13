---
doc_id: L6-FUNCTIONAL-DESIGN-FR-CTX-01
title: Layer context injection 機能仕様
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
  - docs/v2/L6-functional-design/FR-9MODE-01/function-spec.md
  - docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GR-01/function-spec.md
  - HELIX-workflows/helix-process/layer-context-injection.md
artifact_type: design_doc
---

# Layer context injection 機能仕様

## 1. 目的

Layer context injection は、process layer、drive、role、mode を入力に、`owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode` の 6 field を返し、ClaudeCode と Codex の選択空間を同じ HELIX 制約へ揃える機能である。

本仕様は L6 機能設計として、L3 `FR-CTX-01`、L4 Entry and Routing、L5 内部処理設計、`workflow/layer-context-injection` の 6 field 契約を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、context bundle 実装、hook / harness 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-CTX-01` | layer と role に応じた skill、agent、command の注入条件を返す |
| `FR-9MODE-01` | selected mode に対応した injection を求める |
| `FR-PLAN-01` | PLAN dependency / allowed_files を injection context に含める |
| `FR-GR-01` | injection 欠落や Codex/Claude 差分を guardrail input にする |
| `workflow/layer-context-injection` | 6 field 契約と 20 セル構造 |
| `TR-07` | `vmodel-semantics.yaml` 注入契約 |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| CTX-FN-01 | `resolve_injection_cell(layer, drive, role)` | L0-L14 layer, drive, role | 20-cell key | layer 不明を default に丸めない |
| CTX-FN-02 | `load_injection_set(cell)` | cell key, vmodel-semantics, models config | injection set | 6 field 欠落を pass にしない |
| CTX-FN-03 | `validate_injection_set(injection)` | injection set | validation findings | mandatory_agents / commands の未実装を warning / block に分ける |
| CTX-FN-04 | `build_context_bundle(injection, plan)` | injection, PLAN / handover | context bundle | allowed_files / reference_docs / owner_role を保持する |
| CTX-FN-05 | `emit_context_guard_input(bundle)` | bundle | guardrail / doctor input | ClaudeCode だけ効く注入を parity finding にする |
| CTX-FN-06 | `append_context_feedback(bundle)` | bundle, evidence refs | events / metrics / feedback payload | append-only。bundle 生成だけでは closure 不可 |
| CTX-FN-07 | `emit_context_completion_guard_summary(state)` | context state, strict full-flow status | goal audit summary | context injected と full objective completion を分離する |

## 4. Injection Contract

```yaml
layer_context_bundle:
  input:
    layer: L0-L14
    drive: be | fe | db | fullstack
    role: tl | se | pg | qa | docs | security | dba | devops
    mode: Forward | Discovery | Reverse | Incident | Add-feature | Refactor | Retrofit | Research | Recovery
  injection:
    owner_role: string
    mandatory_agents: []
    recommended_agents: []
    recommended_skills: []
    recommended_commands: []
    orchestration_mode: string
  constraints:
    allowed_files: []
    reference_docs: []
    escalation_rules: []
  completion:
    bundle_generated_is_closure: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| 6 field のいずれかが欠落 | `block` or `warning`。policy に従うが pass 不可 |
| layer / drive / role が未定義 | exit code 2 相当 |
| mandatory agent が未実装 | `block` または explicit waiver required |
| recommended command が未実装 | warning。completion 不可 |
| ClaudeCode の hook だけで Codex に注入されない | parity finding |
| bundle 生成のみ | closure 不可 |
| strict full-flow deferred が残る | full objective completion deny |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| CTX-UT-CAND-01 | CTX-FN-01 | layer 不明を default に丸めない |
| CTX-UT-CAND-02 | CTX-FN-02 | 6 field 欠落を pass にしない |
| CTX-UT-CAND-03 | CTX-FN-03 | mandatory と recommended の欠落 severity を分ける |
| CTX-UT-CAND-04 | CTX-FN-04 | allowed_files / reference_docs / owner_role を保持する |
| CTX-UT-CAND-05 | CTX-FN-05 | Codex/Claude parity gap を guardrail input にする |
| CTX-UT-CAND-06 | CTX-FN-06 | feedback append は closure に昇格しない |
| CTX-UT-CAND-07 | CTX-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-CTX-01/unit-test-design.md` は現在タスクでは作成しない。
- `CTX-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- context bundle 実装、hook / harness 接続、mandatory agent enforcement、Codex/Claude parity enforcement は別 PLAN / 承認 / allowed_files / verification commands が必要である。
