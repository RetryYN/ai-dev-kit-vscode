---
doc_id: AUDIT-2026-06-10-HARNESS-EXTERNAL-TOOLS-IMPACT-SCOPE
title: "HARNESS external tools / dependency impact current-scope audit"
status: current
created: 2026-06-10
owner: TL
scope: L4-L6
---

# HARNESS External Tools / Dependency Impact Scope Audit

## Purpose

Confirm that the current correction closes the HARNESS external tools / dependency impact design gap only through L6, and does not install tools or create an L7 deliverable in the current scope.

## Current-Scope Evidence

| Layer | Artifact | Status |
|---|---|---|
| L4 | `docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md` | current-phase design gap closed |
| L5 | `docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md` | current-phase design gap closed |
| L6 | `docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md` | current-phase design gap closed |
| L7 | `docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md` | feature ticket only |

## Explicit Non-Claim

- `docs/v2/L7-test-design/harness-external-tools-impact-単体テスト設計.md` is not present and is not claimed as completed.
- `HEXT-UT-*` is not a current-scope completed test-design artifact.
- MCP server, GitHub MCP Server, Semgrep CE, CodeQL, plugin, VSCode extension, CI job, OAuth, PAT, secret, or env setup was not installed or configured.
- The add-feature PLAN is an approval request, not permission to perform external tool installation or L7 work inside the current task.

## Web Evidence Boundary

| Source | Current use |
|---|---|
| MCP official specification | admission protocol / lifecycle / authorization / tool consent evidence only |
| GitHub MCP Server official documentation | OAuth / PAT / host policy / write-capable tool boundary evidence only |
| Semgrep CE official documentation | `semgrep scan` / rule license / local-or-CI execution boundary evidence only |
| GitHub CodeQL official documentation | CodeQL database / code scanning alerts / SARIF-or-CI route evidence only |

## 2026-06-12 L4-L6 Design Tightening

The Web recheck strengthened the L4-L6 design controls without changing the completion boundary:

- L4 now maps official evidence to controls for tool invocation consent, OAuth/PAT scope, rule license, SARIF/CI route, and candidate-only treatment.
- L5 now requires registry fields for `host_support`, `auth_method`, `secret_storage_policy`, `data_access_scope`, `tool_invocation_consent_required`, `tool_poisoning_review_required`, `output_format`, `sarif_supported`, `ci_surface`, and `failure_mode`.
- L6 now defines `HEXT-FN-09` and `HEXT-FN-10`, plus `HEXT-UT-CAND-01..10` as L6 unit-test-design viewpoints only.
- This recheck did not create `docs/v2/L7-test-design/harness-external-tools-impact-単体テスト設計.md` and did not install, enable, or execute any external tool.

## Contract Evidence

| Check | Expected |
|---|---|
| `test ! -e docs/v2/L7-test-design/harness-external-tools-impact-単体テスト設計.md` | no L7 HEXT artifact |
| `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q` | pass |
| `bats cli/tests/test-helix-l0-l14-flow-contract.bats` | pass |
| `helix doctor check_requirement_drift --json` | L6 focus clean, requirements 31, design_links 31, blocking 0 |

## Completion Boundary

The current phase proves L4-L6 design coverage for HARNESS external tools / dependency impact and records L7 work as a feature ticket. It does not prove external tool installation, HARNESS allowlist implementation, MCP server execution, Semgrep / CodeQL execution, CI/equivalent closure, or recurrence closure.
