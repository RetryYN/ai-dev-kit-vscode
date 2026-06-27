# HELIX V3 — Personal Edition Workflow Contracts

> status: draft contract
> purpose: close G0.5 items #17-#21 for HELIX personal edition
> upstream: [L0](../L0-L14/L0-concept.md), [L1](../L0-L14/L1-requirements.md), [L3](../L0-L14/L3-requirements-spec.md), [C6](doc-workflow-rules.md), [domain glossary](domain-glossary.md)
> rule: every workflow must end in Forward DB convergence or explicit discard.

## 1. Common Contract

All personal-edition workflows are deterministic contracts around AI self-orchestration. LLM output may propose content, but gate decisions and DB projection are machine-readable.

Required fields for every run:

| Field | Meaning |
|---|---|
| `run_id` | Stable workflow run id. |
| `workflow_kind` | `review_loop`, `prompt_interpretation`, `learning_maintenance`, or `upgrade_assist`. |
| `source_artifact_id` | Prompt, PLAN, finding, review, test event, postmortem, or drive run that started the workflow. |
| `forward_return` | Target Forward layer and artifact, or `discard_reason`. |
| `gate_result` | `pass`, `fail`, `conditional`, or `blocked_by_escalation`. |
| `evidence_ref` | Artifact or DB row proving the state transition. |
| `v_pair_ref` | Test-design pair impacted by the workflow. |

Common state machine:

```text
captured -> normalized -> projected -> evaluated -> routed -> verified -> closed
                                  \-> blocked_by_escalation
                                  \-> discarded_with_reason
```

Common invariants:

- `closed` requires `forward_return` or `discard_reason`.
- `blocked_by_escalation` requires an escalation signal and must not auto-resume.
- `verified` requires a matching test-design artifact or explicit no-test waiver.
- `reviewed_at` cannot be earlier than `tests_green_at` for review closure.
- No workflow stores raw secrets, PII, credentials, or raw provider transcripts.

## 2. Review-Loop Workflow

### 2.1 Purpose

Reduce rework by forcing each relevant perspective to produce separate evidence and by preventing one passing perspective from hiding a critical finding in another.

### 2.2 State Machine

| State | Entry | Exit condition | Projection |
|---|---|---|---|
| `review_requested` | PLAN/artifact reaches review gate | viewpoints selected | `review_evidence_registry` pending rows |
| `viewpoints_assigned` | workflow determines required roles | worker/reviewer separation checked | `review_viewpoint` list |
| `evidence_collected` | reviewer evidence submitted | each required viewpoint has verdict | `review_evidence_registry` |
| `critical_closed` | findings exist | critical/high findings closed or explicitly escalated | `findings`, `trace_edges` |
| `test_order_checked` | tests_green_at present | `tests_green_at <= reviewed_at` | `test_results`, `review_evidence_registry` |
| `review_closed` | all checks pass | gate result emitted | `gate_runs` |

### 2.3 Required Viewpoints

| Layer / artifact | Required viewpoints | Optional viewpoints |
|---|---|---|
| L0-L1 concept/requirements | PM, TL, docs | security, operations |
| L3 requirements spec | PM, TL, QA, docs | security |
| L4 basic design | TL, SE, QA, security, docs | perf, UX |
| L5 detailed design | TL, SE, QA, security | DBA, perf |
| L6 functional design | SE, QA, TL | security, docs |
| L7 implementation | QA, TL or cross-agent reviewer | security, perf |

### 2.4 Gate Hook

`review-loop-closure` fails when:

- required viewpoint evidence is missing;
- `worker_model == reviewer_model` for a cross-agent review;
- `tests_green_at > reviewed_at`;
- unresolved critical/high finding remains;
- review evidence points to an artifact that is not in `artifact_registry`.

### 2.5 Test Design Pair

| Test layer | Design case |
|---|---|
| L3 acceptance | critical finding blocks acceptance until closure evidence exists |
| L4 system | mixed viewpoint pass/fail must fail as AND |
| L5 integration | review evidence joins findings and test results by plan/artifact id |
| L6 unit | `evaluate_review_gate(db, plan_id)` positive/negative/boundary fixtures |

## 3. Prompt-Interpretation Workflow

### 3.1 Purpose

Interpret a user prompt from multiple perspectives before planning or execution so that ambiguous scope, missing acceptance criteria, doc/test gaps, and escalation boundaries become visible early.

### 3.2 Required Viewpoints

| Viewpoint | Output | Blocks when |
|---|---|---|
| `scope` | intended work, exclusions, affected layers | scope conflicts with handover/PLAN |
| `acceptance` | observable success criteria | no testable acceptance exists |
| `risk` | technical, schedule, regression risk | high risk lacks mitigation |
| `test` | required V-pair test design | test layer cannot be identified |
| `doc` | required design/doc coverage | required doc kind missing |
| `escalation` | §10 approval signals | prod/auth/payment/PII/secret/license/schema/env/external API present |
| `subagent` | recommended role review or delegation | mandatory role missing for gate |

### 3.3 State Machine

| State | Entry | Exit condition | Projection |
|---|---|---|---|
| `prompt_captured` | user prompt or handover input | prompt id created | `prompt_interpretations` |
| `viewpoints_generated` | viewpoint extraction run | all required viewpoints present | `prompt_interpretations` |
| `conflicts_detected` | interpretations compared | conflicts become findings | `findings` |
| `plan_ready` | no blocking conflict | PLAN draft has acceptance/test/doc coverage | `plan_registry` |
| `blocked_by_escalation` | §10 signal present | human approval required | `guardrail_decisions` |

### 3.4 Subagent Strengthening

Prompt interpretation recommends subagent or role review by deterministic signals:

| Signal | Recommended reviewer |
|---|---|
| auth/authz/payment/PII/secret | security |
| schema/DB/migration/data destruction | DBA/TL |
| external API/infrastructure/env | DevOps/TL |
| UI/a11y/visual/state transition | UX/FE/QA |
| ambiguous requirement or market/product term | PM/PO |
| test strategy gap | QA |
| domain term drift | docs/TL |

The recommendation is advisory unless the target gate marks that reviewer mandatory. Mandatory omissions fail `prompt-interpretation-risk`.

### 3.5 Test Design Pair

| Test layer | Design case |
|---|---|
| L3 acceptance | prompt with PII/auth/prod signal blocks auto-run |
| L4 system | prompt with conflicting scope and handover creates finding |
| L5 integration | prompt_interpretations joins PLAN draft and findings |
| L6 unit | `interpret_prompt(prompt, context)` produces all required viewpoints |

## 4. Learning-Maintenance Workflow

### 4.1 Purpose

Convert repeated findings, review comments, test result events, and postmortems into maintainable improvements without letting the learning loop mutate Forward canon directly.

### 4.2 Candidate Kinds

| Candidate kind | Source | Forward return |
|---|---|---|
| `plan_draft` | repeated finding or failed gate | L1/L3/L4/L5/L6 depending on touched design layer |
| `rule_candidate` | detector false negative or repeated omission | C6 / gate rule map |
| `template_gap` | missing doc section or pair test kind | template_catalog / doc_coverage |
| `debt_item` | accepted risk or deferred issue | issue_queue / future PLAN |
| `runbook_update` | incident/postmortem | L13/L14 |

### 4.3 State Machine

| State | Entry | Exit condition | Projection |
|---|---|---|---|
| `signal_captured` | finding/review/test/postmortem event | source hash recorded | `learning_candidates` |
| `candidate_normalized` | candidate kind assigned | required fields present | `learning_candidates` |
| `impact_mapped` | affected Forward layer selected | forward_return or discard_reason present | `trace_edges` |
| `promotion_reviewed` | reviewer evaluates candidate | promote/defer/discard decided | `review_evidence_registry` |
| `returned_to_forward` | promoted candidate | PLAN/rule/template gap created | `plan_registry`, `template_catalog`, `findings` |
| `discarded` | non-actionable candidate | discard reason stored | `learning_candidates` |

### 4.4 Guardrails

- Learning candidates never edit confirmed Forward artifacts directly.
- A candidate without `forward_return` and without `discard_reason` fails `learning-forward-return`.
- Candidate promotion that touches schema/env/external API/license/PII requires escalation.
- Repeated discarded candidates with the same source pattern create a meta-finding.

### 4.5 Test Design Pair

| Test layer | Design case |
|---|---|
| L3 acceptance | finding produces candidate and requires forward_return |
| L4 system | promoted candidate becomes PLAN draft, not direct artifact mutation |
| L5 integration | candidate joins findings/review/test events/postmortems |
| L6 unit | `promote_learning_candidate(...)` rejects missing forward_return/discard_reason |

## 5. Upgrade-Assist Workflow

### 5.1 Purpose

Handle future dependency/provider/model/platform/HELIX version upgrades as a controlled auxiliary drive, separate from retrofit. Upgrade-assist evaluates future deltas and returns safe work to Forward.

### 5.2 Required PLAN Fields

| Field | Meaning |
|---|---|
| `version_delta` | What changes, from which version/state to which target. |
| `impact_scope` | Affected artifacts, DB tables, commands, providers, docs, tests, and gates. |
| `rollback_condition` | Concrete condition that stops or rolls back the staged adoption. |
| `staged_gate` | Ordered gate sequence for evaluation. |
| `forward_return` | Forward layer and artifact that owns the accepted change. |
| `approval_required` | True when §10 boundary is present. |

### 5.3 State Machine

| State | Entry | Exit condition | Projection |
|---|---|---|---|
| `delta_captured` | version/provider/platform signal | `version_delta` present | `drive_runs` |
| `impact_projected` | affected artifacts identified | impact scope complete | `trace_edges`, `artifact_registry` |
| `risk_gated` | §10 scan complete | approval or safe continuation | `guardrail_decisions` |
| `staged_plan_created` | staged gates listed | rollback condition present | `plan_registry` |
| `forward_returned` | accepted stage | Forward artifact owns implementation | `trace_edges`, `gate_runs` |
| `rolled_back_or_discarded` | stage fails | rollback/discard evidence stored | `drive_runs`, `findings` |

### 5.4 Upgrade-Assist vs Retrofit

| Dimension | Upgrade-assist | Retrofit |
|---|---|---|
| Entry | future version delta | existing configuration drift |
| Goal | assess and safely adopt future change | bring current system back to current canon |
| Output | staged Forward work or discard | L4-L9 correction work |
| Approval | rollback/cutover/schema/env/external API requires approval | config/prod/destructive boundaries require approval |

### 5.5 Test Design Pair

| Test layer | Design case |
|---|---|
| L3 acceptance | missing rollback_condition fails PLAN |
| L4 system | staged gate list maps to affected components and public API |
| L5 integration | drive_runs joins plan_registry and trace_edges |
| L6 unit | `evaluate_upgrade_assist_contract(plan)` rejects missing required fields |

## 6. Forward Convergence Matrix

Every drive mode must converge to Forward DB through explicit artifacts. A drive run without `forward_return` or `discard_reason` is incomplete.

| Drive mode | Entry signal | Required Forward return | DB artifacts | Primary gate/rule |
|---|---|---|---|---|
| design / Forward | descent obligation, planned feature | L0-L6/L7-L14 normal spine | plan_registry, artifact_registry, trace_edges, gate_runs | pair-exists, trace-bidir |
| add-feature | feature addition, scope extension | L1/L3/L4/L5/L6 depending on change | plan_registry, trace_edges, functional_registry | upstream-coverage |
| discovery | unknown requirement, feasibility, PoC | L1/L3/L4-L6 or reject | drive_runs, plan_registry, findings | decision_outcome + forward_return |
| reverse | failure, drift, observed behavior gap | R4 routing to L1/L3/L4/L5/gap-only | drive_runs, findings, trace_edges | reverse routing closure |
| recovery | agent runaway, forced stop, context exhaustion | last safe Forward layer or blocked handover | guardrail_decisions, drive_runs, findings | recovery approval |
| incident | prod/hotfix signal | L1/L3/L4-L6/L14 with approval | findings, guardrail_decisions, runbook evidence | incident approval |
| refactor | code smell, debt, behavior unchanged | L7 only unless design boundary changes | plan_registry, trace_edges, test_results | behavior unchanged + pair closure |
| retrofit | dependency/config drift in current canon | L4-L9 | drive_runs, plan_registry, trace_edges | retrofit forward_return |
| scrum | user feedback iteration | Reverse fallback then Forward | feedback_events, drive_runs, plan_registry | feedback closure |
| research | tech decision, ADR needed | L1 or L4 ADR/design input | artifact_registry, trace_edges, findings | research evidence |
| screen-design | screen gap, wireframe missing | L2 then downstream L3/L4 as needed | screens, screen_trace, artifact_registry | screen coverage |
| frontend-design | a11y, visual, token drift, UX feedback | L10 and paired L2/L4/L6 as needed | screens, screen_trace, quality_signals | FE governance |
| design-bottomup | backend-derived screen or data entity | Discovery synthesis then L3-L6 | artifact_registry, trace_edges, findings | bottom-up slot closure |
| upgrade-assist | version/provider/platform delta | L4-L9, or L1/L3 if requirement changes | drive_runs, plan_registry, trace_edges, gate_runs | upgrade-assist-contract |

Convergence invariants:

- Forward Control owns final canon even when entry mode is not Forward.
- Drive mode output must be projected into DB before any detector can pass.
- A drive can return `gap-only` only when the finding is documented and intentionally not promoted.
- Any drive touching §10 boundary must set `approval_required=true`.

## 7. Gate And Test Summary

| Workflow | Gate rule | Acceptance test | System test | Integration test | Unit test |
|---|---|---|---|---|---|
| review-loop | review-loop-closure | AT-V3-16 | ST-V3-10 | review evidence joins findings/test_results | UT-DET-18 |
| prompt-interpretation | prompt-interpretation-risk | AT-V3-17 | ST-V3-09 | interpretations join PLAN/findings | UT-DET-19 |
| learning-maintenance | learning-forward-return | AT-V3-18 | ST-V3-11 | candidates join source events/trace_edges | UT-DET-20 |
| upgrade-assist | upgrade-assist-contract | AT-V3-19 | staged gate/rollback scenario | drive_runs join plan_registry/trace_edges | UT-DET-21 |

## 8. Open Implementation Gaps

- C1 table columns for the personal-edition projection tables are still deferred to L7.
- Gate rule wiring and runnable tests are not implemented in code yet.
- Independent cross-agent review evidence for this workflow contract is not attached yet.
