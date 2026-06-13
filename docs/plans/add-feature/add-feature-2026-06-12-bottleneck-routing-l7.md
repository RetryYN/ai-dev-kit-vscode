---
plan_id: add-feature-2026-06-12-bottleneck-routing-l7
title: "Action(add-feature): bottleneck routing and recurrence closure L7 entry point"
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
approval_boundary: "This PLAN is only a ticket. Bottleneck detector implementation, route execution, HELIX DB writes, recurrence closure, CI/equivalent wiring, and fail-close promotion require explicit approval."
unlock_conditions:
  - bottleneck_candidate_routing
  - recurrence_closure
parent_design:
  - docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  - docs/v2/L6-functional-design/FR-GATE-01/function-spec.md
  - docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md
  - docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md
dependencies:
  requires:
    - docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml
    - docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml
    - docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml
  blocks: []
generates:
  - artifact_path: cli/lib/bottleneck_routing.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_bottleneck_routing.py
    artifact_type: test
  - artifact_path: cli/helix-bottleneck
    artifact_type: cli_extension
forward_return: "L1-L6 bottleneck readiness gap -> approved L7 TDD implementation -> routed candidate evidence -> recurrence closure evidence."
related_docs:
  - docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml
  - docs/v2/audit/2026-06-12-full-objective-gap-status.yaml
---

# Bottleneck Routing and Recurrence Closure L7 Entry Point

## 1. Purpose

This add-feature ticket records the implementation entry point for bottleneck
classification, routing, and recurrence closure. The L1-L6 design work defines
signal sources, cross-axis aggregation, owner routing, and closure boundaries,
but the current task does not implement route execution or close recurrence.

This document is a ticket only. It is not L7 implementation evidence and does
not close any bottleneck by itself.

## 2. Scope After Approval

| Area | L7 work after approval | Boundary |
|---|---|---|
| Signal routing | Implement bottleneck candidate normalization from requirement drift, pair balance, deferred gates, feedback, dependency, external tool, and plan registry signals | Candidate routing is not remediation closure |
| Cross-axis aggregation | Implement aggregate signal calculation for drift, doc-connection, regression-dependency, and feedback-loop patterns | No automatic workflow execution |
| Owner assignment | Produce owner role, priority floor, affected layer/pair, and next plan or feature ticket | No auto-apply |
| Recurrence closure | Record closure evidence only after approved implementation and verification evidence exist | No DB write adoption without approval |

## 3. Non-Scope

- Current task execution of L7.
- Creating L7 test-design artifacts before approval.
- HELIX DB write adoption or schema migration.
- External tool installation/execution.
- CI/equivalent required status setup.
- Treating a routed candidate as remediation closure.

## 4. Acceptance After Approval

- A failing test first proves that representative bottleneck signals cannot be
  normalized and routed.
- Every routed candidate includes signal id, source evidence, category, affected
  layer/pair, impact scope, owner, next plan/ticket, and completion boundary.
- Cross-axis aggregation preserves priority floors and never auto-executes a
  workflow.
- Recurrence closure is impossible without implementation evidence,
  verification evidence, and an approved feedback record.
- Contract tests keep this ticket from being counted as completion evidence.

## 5. Current Status

Draft only. Approval is required before any L7 implementation, DB write,
route execution, recurrence closure, or CI/equivalent wiring.
