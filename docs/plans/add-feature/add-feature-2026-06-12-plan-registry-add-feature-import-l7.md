---
plan_id: add-feature-2026-06-12-plan-registry-add-feature-import-l7
title: "Action(add-feature): plan_registry add-feature ticket import L7 entry point"
plan_scope: action
workflow: add-feature
kind: add-impl
layer: L7
process_layer: L7
drive: be
status: draft
tl_review: approve  # draft boundary ticket の push 承認のみ (TL L1-L6 review 2026-06-13: 境界妥当・prior L1-L6 evidence 有り・design_substitute=0)。L7 実装承認ではない (status=draft 維持、approval_required_before_* 参照)
created: 2026-06-12
owner: TL
current_task_scope: feature_ticket_only
approval_required_before_l7_work: true
approval_boundary: "This PLAN is only a ticket. plan_registry import changes, DB write adoption, hook changes, migration decisions, CI/gate connection, and fail-close promotion require explicit approval."
parent_design:
  - HELIX-workflows/helix-process/db-auto-registration.md
  - HELIX-workflows/helix-process/add-feature-workflow.md
dependencies:
  requires:
    - cli/lib/plan_registry.py
    - docs/plans/add-feature/
    - docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml
  blocks: []
generates:
  - artifact_path: cli/lib/plan_registry.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_registry.py
    artifact_type: test
  - artifact_path: docs/commands/
    artifact_type: docs
forward_return: "L1-L6 DB registration readiness gap -> approved L7 TDD implementation -> plan_registry import evidence -> HELIX DB registration closure."
related_docs:
  - HELIX-workflows/helix-process/db-auto-registration.md
  - HELIX-workflows/helix-process/add-feature-workflow.md
  - docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml
  - docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml
unlock_conditions:
  - plan_registry
  - plan_registry_import
  - add_feature
---

# Plan Registry Add-feature Ticket Import L7 Entry Point

## 1. Purpose

This add-feature ticket records a design gap found during the L1-L6 DB registration readiness audit: `plan_registry.bulk_import` currently discovers `PLAN-*.md` and `ADR-*.md`, while current deferred implementation entry points are stored as `docs/plans/add-feature/add-feature-*.md`.

The current task does not change `plan_registry`, write to HELIX DB, add hooks, or create L7 test-design artifacts. This PLAN is the required entry point before making add-feature ticket import behavior executable.

The full-objective gap ledger treats this ticket as the route for `plan_registry`,
`plan_registry_import`, and `add_feature` unlocks. None of those unlocks are
satisfied until this ticket is explicitly approved and the implementation is
verified.

## 2. Scope After Approval

If this PLAN is explicitly approved, the implementation must start test-first and stay inside the generated artifact list unless the approver expands `allowed_files`.

| Area | L7 work after approval | Boundary |
|---|---|---|
| Import discovery | Extend or route plan import so approved `docs/plans/add-feature/add-feature-*.md` tickets can be registered intentionally | Do not silently import arbitrary markdown |
| Frontmatter contract | Validate `plan_id`, `workflow`, `kind`, `status`, `layer`, approval boundary, and generated artifact metadata | Do not treat draft ticket registration as implementation completion |
| DB write evidence | Record import result and failure reasons through existing plan registry surfaces | No schema migration unless separately approved |
| Guard behavior | Keep unapproved add-feature tickets visible as deferred work, not pass evidence | No fail-close promotion until local evidence is stable and approved |

## 2.1 Unlock Conditions

- `plan_registry`: approved registry write or read/write surface accepts supported add-feature metadata with deterministic validation results.
- `plan_registry_import`: `docs/plans/add-feature/add-feature-*.md` import is explicitly supported and tested without broad markdown ingestion.
- `add_feature`: draft add-feature tickets remain visible as deferred routes and cannot be interpreted as implementation or completion evidence.

## 3. Non-Scope

- Current task execution of L7.
- Creating L7 test-design artifacts before this ticket is approved.
- Schema migration or destructive DB operation.
- Auto-applying candidates or changing feature status from draft to approved.
- CI workflow edits or required status check setup.
- External API, credentials, secrets, env, production config, or license changes.
- Marking strict full-flow completion.

## 4. Acceptance After Approval

- A failing test first proves that a representative `docs/plans/add-feature/add-feature-*.md` entry is not imported or is imported without the required boundary metadata.
- The approved implementation imports only explicitly supported add-feature ticket shapes.
- Draft add-feature ticket registration remains `ticket_is_completion_evidence=false`.
- `plan_registry.bulk_import` reports deterministic success / failure counts for add-feature entries.
- `python3 -m pytest cli/lib/tests/test_plan_registry.py -q` passes.
- `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q` passes.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.

## 5. Current Status

Draft only. This is a feature ticket, not a completed L7 deliverable.
