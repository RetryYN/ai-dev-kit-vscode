---
plan_id: add-feature-2026-06-13-contract-design-phase-label-retrofit
title: "Action(add-feature): D-API/D-DB/D-CONTRACT phase label retrofit entry point"
plan_scope: action
workflow: add-feature
kind: add-design
layer: L5-L6
process_layer: L5
drive: be
status: draft
tl_review: approve  # draft boundary ticket の push 承認のみ (TL L1-L6 review 2026-06-13: 境界妥当・prior L1-L6 evidence 有り・design_substitute=0)。L7 実装承認ではない (status=draft 維持、approval_required_before_* 参照)
created: 2026-06-13
owner: TL
current_task_scope: feature_ticket_only
approval_required_before_contract_edit: true
approval_required_before_l7_work: true
approval_required_before_implementation: true
approval_boundary: "This PLAN is only a ticket. Editing D-API/D-DB/D-CONTRACT semantics, schema-like snippets, gate enums, migration behavior, CI/equivalent checks, HELIX DB state, or L7 implementation requires explicit approval."
unlock_conditions:
  - contract_design_phase_label_retirement
  - contract_semantics_preserved
current_scope_non_actions:
  contract_edit_performed: false
  schema_migration_done: false
  l7_work_performed: false
  helix_db_write_performed: false
  ci_or_equivalent_connected: false
contract_semantics_preservation_matrix:
  - surface: D-API
    allowed_after_approval: terminology_and_carry_boundary_labels_only
    forbidden_without_expanded_approval:
      - endpoint_shape_change
      - adapter_behavior_change
      - request_response_contract_change
    required_evidence_after_approval:
      - review_diff_is_label_only
      - api_contract_snippet_comparison
  - surface: D-DB
    allowed_after_approval: terminology_and_migration_carry_labels_only
    forbidden_without_expanded_approval:
      - table_shape_change
      - migration_id_change
      - rollback_semantics_change
    required_evidence_after_approval:
      - review_diff_is_label_only
      - db_contract_snippet_comparison
  - surface: D-CONTRACT
    allowed_after_approval: terminology_and_gate_reference_labels_only
    forbidden_without_expanded_approval:
      - event_schema_change
      - enum_value_change
      - validation_behavior_change
    required_evidence_after_approval:
      - review_diff_is_label_only
      - event_contract_snippet_comparison
external_reference_basis:
  - source_id: OPENAPI-SPEC-3-2-0
    url: https://spec.openapis.org/oas/latest.html
    source_type: official_spec
    checked_on: 2026-06-13
    applies_to:
      - D-API
    usage: API description semantics and contract-shape preservation boundary
  - source_id: JSON-SCHEMA-VALIDATION-2020-12
    url: https://json-schema.org/draft/2020-12/json-schema-validation
    source_type: official_spec
    checked_on: 2026-06-13
    applies_to:
      - D-CONTRACT
    usage: event/schema validation semantics preservation boundary
  - source_id: POSTGRESQL-ALTER-TABLE-CURRENT
    url: https://www.postgresql.org/docs/current/sql-altertable.html
    source_type: official_docs
    checked_on: 2026-06-13
    applies_to:
      - D-DB
    usage: table-shape and migration-impact approval boundary
parent_design:
  - HELIX-workflows/HELIX-process-L0-L14.md
  - docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml
  - docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml
observed_gap:
  - docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md
dependencies:
  requires:
    - docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml
    - docs/v2/audit/2026-06-12-full-objective-gap-status.yaml
  blocks: []
generates:
  - artifact_path: docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md
    artifact_type: design_contract
  - artifact_path: docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md
    artifact_type: design_contract
  - artifact_path: docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md
    artifact_type: design_contract
forward_return: "Current L0-L14 terminology -> approved contract-design retrofit -> D-API/D-DB/D-CONTRACT trace evidence -> L1-L6 audit remains clean."
related_docs:
  - docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml
  - docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml
---

# D-API/D-DB/D-CONTRACT Phase Label Retrofit Entry Point

## 1. Purpose

The L1-L6 audit found that several contract-design drafts still contain
PLAN-084 era `Phase 4.A/B/C` carry labels and old gate examples. The current
Forward flow uses L7 for implementation and G7 for implementation completion,
but these files are D-API / D-DB / D-CONTRACT surfaces. Editing them directly
may alter contract meaning, schema-like snippets, or migration guidance.

This add-feature ticket records the approval boundary for a later contract
design retrofit. It is not implementation evidence, not L7 evidence, and not
full-goal completion evidence.

## 2. Scope After Approval

| Area | Approved retrofit work | Boundary |
|---|---|---|
| D-API labels | Rewrite old `Phase 4.A/B/C` carry labels into current L0-L14 / L7 approved-entry wording | Preserve API behavior and adapter contract unless separately approved |
| D-DB labels | Rewrite old migration / projector carry labels without changing table shape, migration IDs, or rollback semantics | Schema migration requires separate approval |
| D-CONTRACT labels | Rewrite event-envelope carry labels and gate references to current L0-L14 terminology | Do not change event schema, enum values, or validation behavior without approval |
| Audit evidence | Update L1-L6 audit maps so these drafts cannot be mistaken for current completion proof | Audit evidence cannot count as L7 implementation or DB adoption |

## 3. Non-Scope

- Current task execution of the contract edit.
- L7 implementation, unit-test implementation, unit-test execution, or coverage closure.
- D-API / D-DB / D-CONTRACT semantic changes.
- Schema migration or destructive DB operation.
- HELIX DB write adoption.
- CI/equivalent required-status wiring.
- External API, credentials, secrets, env, production config, or license changes.
- Marking full objective completion.

## 4. Acceptance After Approval

- A review diff shows only terminology / carry-boundary changes unless the approver explicitly expands scope.
- D-API / D-DB / D-CONTRACT snippets preserve existing contract semantics.
- Old `Phase 4.A/B/C` implementation carry wording is either replaced with current L7 approved-entry wording or marked as historical PLAN-084 reference.
- `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q` passes.
- `bats cli/tests/test-helix-l0-l14-flow-contract.bats` passes.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.

## 5. Current Status

Draft only. Explicit approval is required before editing D-API, D-DB,
D-CONTRACT, schema-like snippets, runtime code, tests, HELIX DB state, or
CI/equivalent gates.
