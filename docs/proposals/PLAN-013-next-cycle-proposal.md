# PLAN-013 Next-Cycle Improvement Proposal

## Purpose

PLAN-013 reached code-index eligibility completion, but the completion pass exposed manual synchronization work across roadmap DoD, sprint DoD, readiness evidence, and gate state. The next cycle should reduce that manual work and make completion status easier to audit.

## Proposal

| ID | Improvement | Target Layer | Acceptance |
|----|-------------|--------------|------------|
| NC-001 | Add a `helix readiness evidence` report that lists required evidence, detected paths, and missing paths per L7-L11 phase. | L7-L11 | Command exits 0 when all required evidence is present and prints concrete paths. |
| NC-002 | Add a `helix roadmap sync-check` command that compares roadmap DoD, `.helix/task-plan.yaml`, and sprint status. | L3-L7 | PLAN-013-style stale checkbox drift is reported before gate execution. |
| NC-003 | Add G9-G11 regression coverage to the standard Bats command group. | L9-L11 | `helix test --no-pytest --bats-only` includes the G9-G11 route tests. |
| NC-004 | Replace initialized placeholder debt with documented examples outside the active debt register. | L6-L11 | New projects start with zero unresolved debt unless explicitly configured. |

## Non-Goals

- No API contract change.
- No database schema migration beyond existing additive cache fields.
- No production deployment automation change.

## Risks

| Risk | Mitigation |
|------|------------|
| Readiness checks become too prescriptive about file layout. | Keep checks name-based but print recommended paths. |
| Sync-check duplicates gate logic. | Limit sync-check to evidence and status drift; keep pass/fail authority in gates. |
| Standard Bats runtime grows. | Keep G9-G11 tests route-level and avoid expensive AI or external checks. |

## Recommended Next Sprint

| Task | Owner | Estimate |
|------|-------|----------|
| Implement readiness evidence path reporting. | TL | 0.5d |
| Implement roadmap/task-plan/sprint sync-check. | TL | 1.0d |
| Wire G9-G11 tests into standard Bats group if not already included. | TL | 0.5d |
| Move placeholder debt examples out of active register. | TL | 0.5d |

## Exit Criteria

- `./cli/helix readiness check --phase L11 --json` remains ready.
- `./cli/helix gate G11` passes after G10.
- Full local pytest and Bats regression pass.
