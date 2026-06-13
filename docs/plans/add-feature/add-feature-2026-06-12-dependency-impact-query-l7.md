---
plan_id: add-feature-2026-06-12-dependency-impact-query-l7
title: "Action(add-feature): dependency impact query L7 entry point"
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
approval_boundary: "This PLAN is only a ticket. Impact query CLI/API implementation, HELIX DB writes, external tool output ingestion, CI/equivalent wiring, and fail-close promotion require explicit approval."
unlock_conditions:
  - dependency_impact
  - edge_visibility
parent_design:
  - docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-INV-01/function-spec.md
  - docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md
  - docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md
dependencies:
  requires:
    - docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml
    - docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml
    - docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml
  blocks: []
generates:
  - artifact_path: cli/lib/impact_query.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_impact_query.py
    artifact_type: test
  - artifact_path: cli/helix-impact
    artifact_type: cli_extension
forward_return: "L1-L6 dependency impact readiness gap -> approved L7 TDD implementation -> impact query evidence -> HELIX DB dependency visibility closure."
related_docs:
  - docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml
  - docs/v2/audit/2026-06-12-full-objective-gap-status.yaml
---

# Dependency Impact Query L7 Entry Point

## 1. Purpose

This add-feature ticket records the implementation entry point for dependency
and change-impact visibility. The L1-L6 design work defines the required output
shape, dependency edge contract, and scope routing rules, but the current task
does not implement a query CLI/API or write dependency edges to HELIX DB.

This document is a ticket only. It is not L7 implementation evidence and does
not close the full objective.

## 2. Scope After Approval

| Area | L7 work after approval | Boundary |
|---|---|---|
| Impact query | Implement a deterministic query surface from seed to affected plans, design docs, tests, code paths, gates, edges, and feedback refs | Do not treat query output as gate pass evidence |
| Dependency graph | Build dependency edges from existing registries and traces, including relation and confidence | No schema migration unless separately approved |
| Feedback refs | Emit append-only feedback candidates for unknown or broad impact | No auto-apply or recurrence closure |
| CLI/API | Add an approved local command or API surface with stable JSON output | No external tool execution without separate approval |

## 3. Non-Scope

- Current task execution of L7.
- Creating L7 test-design artifacts before approval.
- HELIX DB write adoption or schema migration.
- External tool installation/execution or output ingestion.
- CI/equivalent required status setup.
- Marking dependency visibility or full-goal completion as closed.

## 4. Acceptance After Approval

- A failing test first proves that a representative impact seed cannot produce
  the required output sections.
- The implementation returns `seed`, affected artifacts, affected gates,
  dependency edges, feedback refs, and completion boundary.
- Unknown or broad scope routes to manual review or add-feature/retrofit
  candidate without auto-execution.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.
- Contract tests keep this ticket from being counted as completion evidence.

## 5. Current Status

Draft only. Approval is required before any L7 implementation, DB write,
external tool execution, or CI/equivalent wiring.
