---
doc_id: L6-FUNCTIONAL-DESIGN-FR-DOCTOR-01
title: Doctor aggregate audit 機能仕様
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
  - docs/v2/L6-functional-design/FR-GR-01/function-spec.md
  - docs/v2/L6-functional-design/FR-INV-01/function-spec.md
  - docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
artifact_type: design_doc
---

# Doctor aggregate audit 機能仕様

## 1. 目的

Doctor aggregate audit は、docs / plan / vmodel / db / skill / security / locks / inventory の領域別監査結果を束ね、領域別 summary と全体 summary を返す機能である。

本仕様は L6 機能設計として、L3 `FR-DOCTOR-01`、L4 Audit and Quality、L5 内部処理設計を関数粒度に落とす。現在フェーズでは L6 仕様までを閉じ、L7 単体テスト設計、doctor dispatcher 実装、doctor type subcommand 接続は行わない。

## 2. 上位 Trace

| 上位資産 | 接続 |
|---|---|
| `FR-DOCTOR-01` | 複数監査結果を束ね、領域別または全体の summary を返す |
| `FR-GR-01` | guardrail verdict を doctor summary に入れる |
| `FR-INV-01` | inventory / density finding を summary に入れる |
| `FR-DRIFT-01` | drift route finding を summary に入れる |
| `FR-CHANGEPROP-01` | ratchet regression finding を summary に入れる |
| `DBEV-FN-*` | doctor result を feedback lifecycle に載せる |

## 3. Function Contract

| Function ID | surface | 入力 | 出力 | invariant |
|---|---|---|---|---|
| DOCTOR-FN-01 | `select_doctor_types(request)` | --type, --json, scope | type list | unknown type を all に丸めない |
| DOCTOR-FN-02 | `run_doctor_subchecks(types)` | type list | subcheck result list | 個別失敗を握り潰さず result に保持する |
| DOCTOR-FN-03 | `normalize_doctor_findings(results)` | subcheck results | normalized findings | severity / type / evidence_ref を失わない |
| DOCTOR-FN-04 | `aggregate_doctor_summary(findings)` | normalized findings | domain summary + overall summary | critical 1 件以上で success にしない |
| DOCTOR-FN-05 | `emit_doctor_gate_input(summary)` | summary | gate input / detector finding | critical を advisory に降格しない |
| DOCTOR-FN-06 | `append_doctor_feedback(summary)` | summary, evidence refs | events / metrics / feedback payload | append-only。summary は closure ではない |
| DOCTOR-FN-07 | `emit_doctor_completion_guard_summary(summary)` | summary, strict full-flow status | goal audit summary | local clean と full objective completion を分離する |

## 4. Summary Contract

```yaml
doctor_summary:
  requested_type: docs | plan | vmodel | db | skill | security | locks | inventory | all
  domain_summaries:
    - type: string
      pass: number
      warn: number
      fail: number
      critical: number
      findings: []
  overall:
    pass: number
    warn: number
    fail: number
    critical: number
    exit_code: 0 | 1 | 2
  completion:
    summary_is_goal_completion: false
    l7_artifact_created_in_current_scope: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| unknown doctor type | exit code 1 |
| critical 1 件以上 | exit code 2 + gate fail input |
| subcheck 実行不能 | type summary は fail、all summary は fail 以上 |
| warning のみ | exit code 0 or 1。policy に従うが closure 不可 |
| local L6 focus clean | full objective completion ではない |
| strict full-flow deferred が残る | full objective completion deny |
| feedback append のみ | closure 不可 |

## 6. L6 単体テスト設計観点

本 L6 仕様に対応する単体テスト設計観点は以下に固定する。現在タスクでは L7 test-design artifact を作成しない。

| UT 観点 | 対象 function | 期待 |
|---|---|---|
| DOCTOR-UT-CAND-01 | DOCTOR-FN-01 | unknown type を all に丸めない |
| DOCTOR-UT-CAND-02 | DOCTOR-FN-02 | 個別 subcheck 失敗を result に保持する |
| DOCTOR-UT-CAND-03 | DOCTOR-FN-03 | severity / type / evidence_ref を保持する |
| DOCTOR-UT-CAND-04 | DOCTOR-FN-04 | critical 1 件以上で success にしない |
| DOCTOR-UT-CAND-05 | DOCTOR-FN-05 | critical を gate input に保持する |
| DOCTOR-UT-CAND-06 | DOCTOR-FN-06 | feedback append は closure に昇格しない |
| DOCTOR-UT-CAND-07 | DOCTOR-FN-07 | strict full-flow deferred が残る場合に completion を deny |

## 7. Completion Boundary

- この文書は L6 設計漏れの閉塞証跡であり、L7 実装完了ではない。
- `docs/v2/L7-test-design/FR-DOCTOR-01/unit-test-design.md` は現在タスクでは作成しない。
- `DOCTOR-UT-CAND-*` は L6 の test-design 観点であり、L7 の完了済み UT inventory ではない。
- doctor dispatcher 実装、doctor type subcommand、audit log 分離、push / CI 接続は別 PLAN / 承認 / allowed_files / verification commands が必要である。
