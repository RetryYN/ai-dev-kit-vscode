---
doc_id: L6-FUNCTIONAL-DESIGN-FR-DOCREVIEW-01
title: Doc-review quality gate 機能仕様
status: current_scope_l6_closed
layer: L6
process_layer: L6
pairs_with: L7
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-12
parent_requirements:
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
upstream_design:
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
related_design:
  - docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md
  - docs/v2/L6-functional-design/FR-INV-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GR-01/function-spec.md
  - skills/workflow/doc-review/SKILL.md
artifact_type: design_doc
---

# Doc-review quality gate 機能仕様

## 1. 目的

Doc-review quality gate は、Correctness / Completeness / Consistency / Clarity、業界標準整合、DDD SSoT、V-model 量閉じ性を使って文書品質を review し、`approve / conditional_approve / blocked` を返す機能である。

本仕様は L6 機能設計として、L3 `FR-DOCREVIEW-01`、L4 Audit and Quality、`workflow/doc-review` skill を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、doc-reviewer 呼び出し実装、doctor coverage check 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-DOCREVIEW-01` | 文書品質 review を role 分離で実行し、設計品質の根拠を残す |
| `FR-DOCTOR-01` | doc-review coverage / findings を doctor summary に渡す |
| `FR-INV-01` | review 対象 doc inventory と density を参照する |
| `FR-GR-01` | doc-review 未実施や blocked 判定を guardrail input にする |
| `workflow/doc-review` | 4 視点 + 業界標準 + V-model 量閉じ性 |
| `FR-GLOSSARY-01` | DDD 用語 SSoT / anti-corruption layer の参照先 |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| DOCREV-FN-01 | `select_doc_review_scope(change_set)` | changed docs, line count, layer, gate | review scope | 大規模 doc 変更を軽微扱いしない |
| DOCREV-FN-02 | `build_doc_review_prompt(scope)` | scope, reference docs, prior findings | review prompt | read-only / no-write 制約を保持する |
| DOCREV-FN-03 | `evaluate_doc_review_result(result)` | reviewer output | approve / conditional_approve / blocked | P0 を conditional に降格しない |
| DOCREV-FN-04 | `normalize_doc_review_findings(result)` | reviewer output | normalized findings | 4 視点 / 標準 / V-model 観点を保持する |
| DOCREV-FN-05 | `emit_doc_review_doctor_input(findings)` | findings | doctor / guardrail input | blocked を advisory に降格しない |
| DOCREV-FN-06 | `append_doc_review_feedback(findings)` | findings, evidence refs | events / metrics / feedback payload | append-only。review evidence は closure ではない |
| DOCREV-FN-07 | `emit_doc_review_completion_guard_summary(state)` | state, strict full-flow status | goal audit summary | doc reviewed と full objective completion を分離する |

## 4. Review Contract

```yaml
doc_review_result:
  scope:
    docs: []
    layer: string
    gate: string
  decision: approve | conditional_approve | blocked
  findings:
    - severity: P0 | P1 | P2 | P3
      viewpoint: Correctness | Completeness | Consistency | Clarity | IndustryStandard | VModel
      path: string
      line: number
      recommendation: string
  reviewer:
    role: doc-reviewer
    read_only: true
  completion:
    review_evidence_is_goal_completion: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| P0 1 件以上 | `blocked` |
| P1 6 件以上 | `blocked` |
| P0 0 かつ P1 1-5 件 | `conditional_approve` |
| P0 0 かつ P1 0 件 | `approve` |
| read-only 制約がない reviewer call | guardrail block |
| review evidence のみ | closure 不可 |
| doctor coverage check 未接続 | current scope では remaining |

## 5.1 Finding Vocabulary

Doc-review quality の L6 検出語彙は以下に固定する。

| Finding Type | 意味 |
|---|---|
| `missing_doc_review_scope` | 大規模 doc 変更または gate 対象 doc に review scope が無い |
| `p0_downgraded_to_conditional` | P0 finding を conditional_approve へ降格している |
| `missing_four_viewpoint_findings` | Correctness / Completeness / Consistency / Clarity の観点が欠落している |
| `missing_vmodel_quantity_closure` | V-model 量閉じ性または pair trace の判定根拠が欠落している |
| `read_only_boundary_missing` | reviewer 呼び出しに read-only / no-write 制約が無い |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| DOCREV-UT-CAND-01 | DOCREV-FN-01 | 大規模 doc 変更を軽微扱いしない |
| DOCREV-UT-CAND-02 | DOCREV-FN-02 | read-only / no-write 制約を保持する |
| DOCREV-UT-CAND-03 | DOCREV-FN-03 | P0 を conditional に降格しない |
| DOCREV-UT-CAND-04 | DOCREV-FN-04 | 4 視点 / 標準 / V-model 観点を保持する |
| DOCREV-UT-CAND-05 | DOCREV-FN-05 | blocked を doctor / guardrail input に保持する |
| DOCREV-UT-CAND-06 | DOCREV-FN-06 | feedback append は closure に昇格しない |
| DOCREV-UT-CAND-07 | DOCREV-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-DOCREVIEW-01/unit-test-design.md` は現在タスクでは作成しない。
- `DOCREV-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- doc-reviewer 呼び出し実装、doctor coverage check、review evidence DB 登録、guardrail / CI 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
