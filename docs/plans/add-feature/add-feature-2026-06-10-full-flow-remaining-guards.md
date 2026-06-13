---
plan_id: add-feature-2026-06-10-full-flow-remaining-guards
title: "Action(add-feature): full-flow remaining guards implementation package"
plan_scope: action
workflow: add-feature
kind: add-impl
layer: L8-L14
process_layer: L8-L14
forward_return: "L4-L6 right-arm gate design (re-freeze) -> approved L7 implementation -> right-arm execution evidence (G8:L5↔L8 / G9:L4↔L9 / G12:L3↔L12 / G14:L1↔L14) -> full-flow closure evidence (各右腕 pair の pending gate evidence に帰属)."
drive: be
status: draft
tl_review: approve  # draft boundary ticket の push 承認のみ (TL L1-L6 review 2026-06-13: 境界妥当・prior L1-L6 evidence 有り・design_substitute=0)。L7 実装承認ではない (status=draft 維持、approval_required_before_* 参照)
created: 2026-06-10
owner: TL
current_task_scope: feature_ticket_only
approval_required_before_later_phase_work: true
approval_required_before_implementation: true
approval_boundary: "This PLAN is only a ticket. Right-arm gate implementation, CI/equivalent wiring, feedback closure, schema migration, external tool execution, and fail-close promotion require explicit approval."
unlock_conditions:
  - right_arm_execution_gates
  - ci_or_equivalent
parent_design:
  - docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml
  - docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml
  - docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml
dependencies:
  requires:
    - docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml
    - docs/v2/L7-test-design/full-flow-activation-ledger.yaml
  blocks: []
generates:
  - artifact_path: docs/v2/L8-test-design/
    artifact_type: design_doc
  - artifact_path: docs/v2/L9-test-design/
    artifact_type: design_doc
  - artifact_path: docs/v2/L12-test-design/
    artifact_type: design_doc
  - artifact_path: docs/v2/L14-test-design/
    artifact_type: design_doc
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: python_module
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/helix-harness
    artifact_type: cli_extension
  - artifact_path: cli/lib/harness_monitor.py
    artifact_type: python_module
---

# Full-flow Remaining Guards Implementation Package

## 1. Purpose

This add-feature PLAN is the implementation entry point for the remaining full-flow completion guards. It does not implement the gates by itself and does not expand the active handover scope. It packages the remaining work so the next implementation run can proceed without reinterpreting the objective.

Draft only. This is a feature ticket only. Current task execution of L7/L8-L14 implementation, CI/equivalent wiring, feedback closure, external tool execution, or fail-close promotion is not authorized by this document.

## 2. Guard Work Packages

| Guard | Existing readiness source | Required implementation result |
|---|---|---|
| G8 L5-L8 | `docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml` | Integration-test execution evidence removes G8 from strict full-flow deferred pairs. |
| G9 L4-L9 | `docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml` | System-test execution evidence removes G9 while preserving semantic trace evidence. |
| G12 L3-L12 | `docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml` | Acceptance-test execution evidence removes G12 without reinterpreting L3 requirements. |
| G14 L1-L14 | `docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml` | Operational learning evidence and feedback_closed recurrence evidence remove G14. |
| CI/equivalent | `docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml` | `helix-full-flow-required-gate` records every command assertion as one required CI job or documented local equivalent runner. |
| Feedback closure | `docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml` | Adopted candidate ID links PLAN/PR, gate evidence, CI/equivalent run, HELIX DB event, and recurrence status. |

## 3. Activation Conditions

- Handover Next Action includes the requested implementation files from `right-arm-execution-gates-handover-request.yaml`.
- Each selected guard has owner, allowed_files, acceptance, rollback, and verification commands.
- CI workflow edits require human confirmation.
- Any D-API / D-DB / D-CONTRACT change, schema migration, credential, PII, or infrastructure change requires escalation before implementation.

## 4. Acceptance

- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json` returns `overall_clean=true`, `deferred_count=0`, and `deferred_gates=[]`.
- `helix-full-flow-required-gate` records parsed assertions for requirement drift, L0-L14 contract pytest, L0-L14 contract Bats, feedback loop Bats, and strict full-flow.
- `feedback_closed` evidence references candidate ID, PLAN/PR or local review evidence, gate evidence, CI/equivalent run ID, HELIX DB event ID, and recurrence status.
- `goal-completion-audit.yaml` only changes to complete after all required evidence exists.

## 5. Safety

- `approval_required_before_implementation=true`
- `schema_migration=false`
- `destructive_data_operation=false`
- `auto_apply_feedback_candidates=false`
- `ci_workflow_change=false` until human confirmation
- `external_api_or_credentials=false`
- This PLAN is not completion evidence. It is only an executable entry point for the remaining guards.
