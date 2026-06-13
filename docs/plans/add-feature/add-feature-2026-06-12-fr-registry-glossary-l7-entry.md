---
plan_id: add-feature-2026-06-12-fr-registry-glossary-l7-entry
title: "Action(add-feature): FR-FNREG / FR-GLOSSARY L7 implementation entry point"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
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
approval_boundary: "This PLAN is only a ticket. L7 artifacts, implementation, schema migration, external tool installation, CI connection, and fail-close promotion require explicit approval."
unlock_conditions:
  - registry
  - glossary
agent_slots:
  - role: tl-advisor
    slot_label: "TL - FR-FNREG / FR-GLOSSARY L6 contracts, DB boundary, gate boundary, and fail-close sequence review"
  - role: se
    slot_label: "SE - approved L7 implementation only after TDD tests and allowed_files are fixed"
generates:
  - artifact_path: docs/v2/L7-test-design/FR-FNREG-01/unit-test-design.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/FR-GLOSSARY-01/unit-test-design.md
    artifact_type: design_doc
  - artifact_path: cli/lib/function_registry_checks.py
    artifact_type: python_module
  - artifact_path: cli/lib/glossary_usage_checks.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_function_registry_checks.py
    artifact_type: test
  - artifact_path: cli/lib/tests/test_glossary_usage_checks.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: yaml_config
  - artifact_path: cli/config/ddd-registry.yaml
    artifact_type: yaml_config
dependencies:
  parent: docs/plans/process/process-2026-06-05-registration-detection-cluster.md
  requires:
    - add-feature-2026-06-05-registry-detector-base
    - add-feature-2026-06-05-ddd-registry-coverage
  blocks: []
forward_return: "L6 FR-FNREG / FR-GLOSSARY function specs -> L7 TDD implementation -> doctor warn-only evidence -> optional fail-close / DB / CI adoption in separate approved steps."
related_docs:
  - docs/v2/L6-functional-design/FR-FNREG-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GLOSSARY-01/function-spec.md
  - docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md
  - docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md
  - docs/plans/add-feature/add-feature-2026-06-05-ddd-registry-coverage.md
---

# FR-FNREG / FR-GLOSSARY L7 implementation entry point

## 1. Purpose

This add-feature ticket exists because the current task stops at L6. It records the approved entry point that would be required before implementing:

- `FR-FNREG-01`: functional requirement registry SSoT and automated checks
- `FR-GLOSSARY-01`: domain glossary SSoT and automated usage checks

The current L6 artifacts are complete design inputs, not authorization to start L7.

## 2. Scope After Approval

If this PLAN is explicitly approved, the L7 work must start test-first and stay inside the generated artifact list unless the approver expands `allowed_files`.

| Area | L7 work after approval | Boundary |
|---|---|---|
| FR-FNREG | Create FR-level unit-test design, then implement function-registry checks and doctor surface | Warn-only first; no fail-close without separate approval |
| FR-GLOSSARY | Create FR-level unit-test design, then implement glossary usage checks and doctor surface | Structural usage first; semantic language scan is separately gated |
| HELIX DB | Emit append-only event / metric payloads if an existing DB surface is approved | No schema migration in this PLAN |
| CI / equivalent | Add command bundle only after local evidence is stable | Required status check setup is separate approval |

## 3. Non-Scope

- Current task execution of L7.
- Schema migration or new HELIX DB table creation.
- External MCP server, plugin, Semgrep, CodeQL, or other tool installation.
- Fail-close promotion of glossary / registry checks.
- Changing authentication, secrets, env, production config, or license posture.
- Marking strict full-flow completion.

## 4. Acceptance After Approval

- `docs/v2/L7-test-design/FR-FNREG-01/unit-test-design.md` and `docs/v2/L7-test-design/FR-GLOSSARY-01/unit-test-design.md` exist and trace back to the L6 function IDs.
- Tests are written before implementation and fail for the missing behavior.
- Implementation passes the new tests and does not regress existing doctor / registry tests.
- Doctor output separates candidate findings, advisory findings, fail-close findings, and closure evidence.
- HELIX DB feedback writes, if approved, are append-only and do not require schema migration.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json` still refuses full completion until G8/G9/G12/G14, CI/equivalent, and feedback closure are actually implemented.

## 5. Current Status

Draft only. This is a feature ticket, not a completed L7 deliverable.
