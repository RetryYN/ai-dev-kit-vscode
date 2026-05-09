---
plan_id: PLAN-001
title: "PLAN-001: PoC Skill Canonical Fallback"
status: draft
created: 2026-05-04
finalized: null
author: Opus (PM)
related: []
---
# PLAN-001: PoC Skill Canonical Fallback

Status: superseded archival draft / not finalized
Created: 2026-05-04
Plan state: `.helix/plans/PLAN-001.yaml`
Superseded by: `skills/workflow/poc/SKILL.md`

## Purpose

This document preserves a tracked canonical reference for PLAN-001 after the
original draft source path (`/tmp/helix-plan-source-poc.txt`) became
unavailable. It exists to make cross-plan references resolvable without
pretending that PLAN-001 has passed PLAN review or finalize.

PLAN-001 remains a draft in `.helix/plans/PLAN-001.yaml` for audit accuracy,
but it is excluded from the completion denominator. The current operational
contract is the PoC skill, not this unrecoverable draft.

## Current Decision

- PLAN-001 is superseded by the G1.5 PoC workflow skill.
- The executable process source is `skills/workflow/poc/SKILL.md`.
- The PoC design template is
  `skills/workflow/poc/references/poc-design-template.md`.
- Cross-plan consumers must treat this document as an archival pointer, not as
  an approved implementation plan.
- New PoC workflow changes must use the PoC skill or a new PLAN, not PLAN-001.

## Recovery Notes

The PLAN YAML previously pointed to:

```text
/tmp/helix-plan-source-poc.txt
```

That file is outside the repository and is not present in the current
workspace. Because the source cannot be recovered from git or the current
filesystem, this tracked fallback records the valid repository-local references
and preserves the draft status explicitly.

## PoC Contract Summary

PLAN-001 covers the G1.5 PoC workflow only:

- define kill criteria before starting a PoC
- keep the PoC scope minimal and timeboxed
- avoid production data and production-impacting changes
- produce a yes/no/defer result with evidence
- connect confirmed results to L2, or rejected results back to withdrawal or
  tech-selection

## Non-Goals

- This document does not finalize PLAN-001.
- This document does not introduce a new PoC implementation.
- This document does not override `skills/workflow/poc/SKILL.md`.
- This document does not authorize production, auth, PII, payment, license, or
  infrastructure decisions.

## Closure Decision

Decision date: 2026-05-04
Decision: supersede PLAN-001 with `skills/workflow/poc/SKILL.md`

Rationale:

- the original PLAN source is unrecoverable
- finalizing from a reconstructed fallback would weaken audit accuracy
- the PoC workflow already has a repository-local operational source
- future changes can be planned through a fresh PLAN with complete evidence

PLAN-001 is therefore closed as an archival/superseded draft. It should remain
`status: draft` in PLAN YAML and should not be counted as an active incomplete
PLAN.
