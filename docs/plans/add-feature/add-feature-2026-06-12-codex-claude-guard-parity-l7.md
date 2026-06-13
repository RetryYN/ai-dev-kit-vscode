---
plan_id: add-feature-2026-06-12-codex-claude-guard-parity-l7
title: "Action(add-feature): Codex / Claude guard parity L7 implementation entry point"
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
approval_boundary: "This PLAN is only a ticket. L7 test-design artifacts, implementation, CI/gate connection, schema migration, external tool installation, and fail-close promotion require explicit approval."
unlock_conditions:
  - runtime_guard_parity
agent_slots:
  - role: tl-advisor
    slot_label: "TL - Codex/Claude parity scope, guard severity, and hook-to-harness boundary review"
  - role: se
    slot_label: "SE - approved L7 implementation only after TDD tests and allowed_files are fixed"
generates:
  - artifact_path: docs/v2/L7-test-design/codex-claude-guard-parity-単体テスト設計.md
    artifact_type: design_doc
  - artifact_path: cli/lib/codex_post_validation.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_codex_post_validation.py
    artifact_type: test
  - artifact_path: cli/tests/test-helix-codex-write-audit.bats
    artifact_type: bats_test
  - artifact_path: cli/helix-codex
    artifact_type: cli_extension
  - artifact_path: helix/CODEX_RUNTIME_ADAPTER.md
    artifact_type: runtime_doc
dependencies:
  parent: docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml
  requires:
    - docs/v2/L6-functional-design/FR-CTX-01/function-spec.md
    - docs/v2/L6-functional-design/FR-GR-01/function-spec.md
    - docs/v2/L6-functional-design/whole-source-coverage-機能設計.md
  blocks: []
forward_return: "L6 guard parity design contracts -> L7 TDD implementation -> warn-only Codex parity evidence -> optional fail-close / CI / DB adoption in separate approved steps."
related_docs:
  - docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml
  - docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml
  - docs/v2/L6-functional-design/FR-CTX-01/function-spec.md
  - docs/v2/L6-functional-design/FR-GR-01/function-spec.md
  - docs/v2/L6-functional-design/whole-source-coverage-機能設計.md
---

# Codex / Claude Guard Parity L7 Implementation Entry Point

## 1. Purpose

This add-feature ticket exists because the current task stops at L6. The L1-L6 audit found guard surfaces where Codex already has runtime evidence and guard surfaces that are only L6 design contracts. This ticket is the required entry point before implementing any additional Codex runtime guard or treating ClaudeCode hook behavior as Codex parity.

## 2. Scope After Approval

If this PLAN is explicitly approved, the work must start test-first and stay inside the generated artifact list unless the approver expands `allowed_files`.

| Area | L7 work after approval | Boundary |
|---|---|---|
| Context injection parity | Add tests and implementation so Codex receives or detects missing layer constraints described by `FR-CTX-01` | Warn-only first; no mandatory-agent fail-close without separate approval |
| Guardrail parity axis | Add tests and implementation for `codex_claude_parity` verdicts described by `FR-GR-01` | No CI/gate blocking until local evidence is stable and approved |
| Hook-to-harness parity | Extend Codex post-validation or harness checks where ClaudeCode hook-only coverage would otherwise be invisible | No raw Codex/Claude fallback and no unapproved hook rewrite |
| Evidence registration | Emit machine-readable evidence that links finding ID, source refs, and affected guard surface | Append-only evidence only; no schema migration in this PLAN |

## 3. Non-Scope

- Current task execution of L7.
- Creating the L7 test-design artifact before this ticket is approved.
- Schema migration or new HELIX DB table creation.
- External MCP server, plugin, Semgrep, CodeQL, or other tool installation.
- CI workflow edits or required status check setup.
- Fail-close promotion of parity findings.
- Changing authentication, secrets, env, production config, or license posture.
- Marking strict full-flow completion.

## 4. Acceptance After Approval

- The first change is a failing test that proves the selected Codex/Claude parity gap.
- The L7 test-design artifact traces each implemented behavior to `FR-CTX-01`, `FR-GR-01`, or whole-source coverage.
- Codex evidence distinguishes `codex_runtime_tested`, `l6_design_only`, `future_plan_required`, `warn`, and `block` statuses.
- ClaudeCode hook-only behavior cannot count as parity closure unless a Codex runtime, harness, doctor, or post-validation evidence path exists.
- New findings include guard surface ID, source refs, affected runtime, severity, and remediation.
- `python3 -m pytest cli/lib/tests/test_codex_post_validation.py -q` passes.
- `bats cli/tests/test-helix-codex-write-audit.bats` passes.
- `helix doctor check_requirement_drift --json` remains clean for L6 focus.
- `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json` still refuses full completion until G8/G9/G12/G14, CI/equivalent, and feedback closure are actually implemented.

## 5. Current Status

Draft only. This is a feature ticket, not a completed L7 deliverable.
