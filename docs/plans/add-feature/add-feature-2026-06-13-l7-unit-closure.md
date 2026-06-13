---
plan_id: add-feature-2026-06-13-l7-unit-closure
title: "Action(add-feature): L7 unit implementation, execution, and coverage closure entry point"
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
approval_boundary: "This PLAN is only a ticket. L7 implementation, unit-test implementation, unit-test execution, coverage closure, HELIX DB writes, CI/equivalent wiring, and fail-close promotion require explicit approval."
unlock_conditions:
  - l7_unit
  - coverage_closure
parent_design:
  - docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml
  - docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md
  - docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml
dependencies:
  requires:
    - docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml
    - docs/v2/audit/2026-06-12-full-objective-gap-status.yaml
  blocks: []
generates:
  - artifact_path: cli/lib/tests/
    artifact_type: test
  - artifact_path: cli/lib/
    artifact_type: python_module
forward_return: "L6 function specs and unit-test design -> approved L7 test-first implementation -> unit execution evidence -> coverage closure evidence."
related_docs:
  - docs/v2/audit/2026-06-12-full-objective-gap-status.yaml
  - docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml
---

# L7 Unit Implementation, Execution, and Coverage Closure Entry Point

## 1. Purpose

This add-feature ticket records the approval boundary for the L7 work implied
by the L1-L6 balance audit. The current task closes design and unit-test-design
coverage through L6 only. It does not authorize unit-test implementation,
production implementation, test execution, or coverage closure.
This ticket is not completion evidence and does not prove any L7 deliverable.

## 2. Scope After Approval

| Area | L7 work after approval | Boundary |
|---|---|---|
| Unit tests | Implement tests from the L6 unit-test-design viewpoints before implementation | Test design is already L6; do not create new L7 test-design artifacts without approval |
| Implementation | Implement only the approved functions or detectors covered by the failing tests | Stay inside approved `allowed_files` |
| Execution | Run the approved unit test commands and record command evidence | Execution evidence is not full-flow closure by itself |
| Coverage | Record coverage closure for the approved scope | Coverage closure cannot imply G8/G9/G12/G14 or full-goal completion |

## 3. Non-Scope

- Current task execution of L7.
- Creating L7 test-design artifacts before approval.
- HELIX DB write adoption or schema migration.
- External tool installation or execution.
- CI/equivalent required status setup.
- Marking the full objective complete.

## 4. Acceptance After Approval

- Tests are written first from the L6 unit-test-design viewpoints.
- The first run fails for the missing implementation.
- Implementation passes the new tests and preserves existing L1-L6 contract tests.
- Coverage evidence is recorded for the approved scope only.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json` still refuses full completion until all later-phase execution gates and feedback/CI/DB boundaries are closed.

## 5. Current Status

Draft only. Approval is required before any L7 implementation, unit-test
implementation, unit-test execution, coverage closure, DB write, external tool
execution, or CI/equivalent wiring.
