---
plan_id: add-feature-2026-06-13-phase-enum-l0-l14-runtime-retrofit
title: "Action(add-feature): L0-L14 phase enum runtime retrofit entry point"
plan_scope: action
workflow: add-feature
kind: add-impl
layer: L7
process_layer: L7
drive: be
status: draft
tl_review: approve  # draft boundary ticket の push 承認のみ (TL L1-L6 review 2026-06-13: 境界妥当・prior L1-L6 evidence 有り・design_substitute=0)。L7 実装承認ではない (status=draft 維持、approval_required_before_* 参照)
created: 2026-06-13
owner: TL
current_task_scope: feature_ticket_only
approval_required_before_l7_work: true
approval_required_before_implementation: true
approval_boundary: "This PLAN is only a ticket. Updating runtime phase enums, handover validation, tests, migration behavior, CI/equivalent checks, or HELIX DB state requires explicit approval."
unlock_conditions:
  - runtime_phase_enum
  - handover_validation
parent_design:
  - HELIX-workflows/HELIX-process-L0-L14.md
  - docs/design/D-STATE-SPEC.md
  - cli/templates/patterns/pattern.yaml
  - docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml
observed_gap:
  - cli/lib/handover.py
  - cli/tests/test-handover.bats
observed_metadata_gap:
  current_json_legacy_task_title: true
  current_json_legacy_phase_label: true
  task_retitle_update_command_available_now: false
  next_action_must_remain_authoritative: true
  force_dump_required_for_retitle_without_runtime_change: true
  force_dump_allowed_without_approval: false
dependencies:
  requires:
    - docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml
    - docs/v2/audit/2026-06-12-full-objective-gap-status.yaml
  blocks: []
generates:
  - artifact_path: cli/lib/handover.py
    artifact_type: python_module
  - artifact_path: cli/tests/test-handover.bats
    artifact_type: bats_test
  - artifact_path: cli/templates/state-machine.yaml
    artifact_type: state_machine_definition
forward_return: "Current L0-L14 state specification -> approved L7 runtime enum retrofit -> handover/state-machine validation evidence -> L1-L6 audit remains clean."
related_docs:
  - docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml
  - docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml
---

# L0-L14 Phase Enum Runtime Retrofit Entry Point

## 1. Purpose

The current task aligned the L1-L6 documentation and audit surfaces to the
user-confirmed L0-L14 flow. A remaining runtime gap exists where handover phase
validation and its Bats coverage still describe the old `L1-L11` phase enum.
The active `CURRENT.json` can also keep a legacy L7 task title or phase label
because `helix handover update` does not currently expose a safe task retitle
operation. That machine metadata must not override `CURRENT.md` Next Action.
This ticket records the approval boundary for fixing that runtime gap later.

This add-feature ticket is feature ticket only. It is not completion evidence,
not implementation evidence, and does not prove L7 completion.

## 2. Scope After Approval

| Area | L7 / retrofit work after approval | Boundary |
|---|---|---|
| Handover validation | Update phase validation from old `L1-L11` wording to the approved L0-L14 contract | Preserve stale detection and current Next Action boundary semantics |
| Handover metadata | Add a safe retitle / phase metadata update path or equivalent validated state refresh | Do not require `dump --force` for routine title correction without explicit approval |
| Tests | Update Bats coverage so invalid and valid phase cases reflect L0-L14 | Test-first; do not weaken current stale / owner / status guards |
| State machine | Reconcile runtime state-machine definitions with `docs/design/D-STATE-SPEC.md` if required | Schema or DB migration requires separate approval |
| Audit evidence | Record read-only proof that current handover titles cannot authorize L7 work | Evidence cannot count as L7 implementation or full-goal closure |

## 3. Non-Scope

- Current task execution of this runtime retrofit.
- Unit-test implementation or execution under the current task.
- Coverage closure.
- HELIX DB write adoption or schema migration.
- CI/equivalent required-status wiring.
- Any change that authorizes L7 from the legacy handover task title.

## 4. Acceptance After Approval

- A failing test demonstrates the old `L1-L11` phase enum gap.
- Runtime validation accepts the approved Forward L0-L14 phase vocabulary.
- Handover Next Action remains authoritative over legacy CURRENT.json title and pending entries.
- A legacy CURRENT.json task title or phase label cannot authorize L7 work and
  cannot override the user-confirmed L1-L6 boundary.
- Task retitle / phase metadata correction has a non-destructive, validated
  command path or an explicitly documented approval boundary.
- `bats cli/tests/test-handover.bats` passes.
- `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q` passes.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.

## 5. Current Status

Draft only. Explicit approval is required before editing runtime validation,
tests, state-machine definitions, DB state, or CI/equivalent checks.
