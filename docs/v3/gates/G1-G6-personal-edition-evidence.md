# HELIX V3 — G1/G3/G4/G5/G6 Personal Edition Evidence

> status: design evidence
> scope: L1/L3/L4/L5/L6 gate evidence for HELIX personal edition additions
> upstream: [G0.5 evidence](G0.5-l0-to-l1-handoff.md), [personal-edition gate wiring](../engine/personal-edition-gate-wiring.md)

## 1. Gate Evidence Summary

| Gate | Layer | Evidence | implementation_status | Status |
|---|---|---|---|---|
| G1 | L1 requirements | L1 accepts L0 handoff, defines BR/FR/NFR/OT for AI self-run, templates, review/prompt/learning, upgrade-assist | design-evidence | design-evidence pass |
| G3 | L3 requirements spec | L3 defines REQ-AUTO/TPL/REV/PRM/LRN/UPG and AT-V3-14..19 | design-evidence | design-evidence pass |
| G4 | L4 basic design | L4 defines C7-C10 and ST-V3-08..11 | design-evidence | design-evidence pass |
| G5 | L5 detailed design | L5 defines personal table/data projection rows and IT-V3-07..09; column contract now frozen in schema contract | design-evidence | design-evidence pass |
| G6 | L6 functional design | L6 defines FN-DET-17..21, DbC blocks, and UT-DET-17..21 | design-evidence | design-evidence pass |

## 2. Gate Rule Coverage

| Rule | G1 | G3 | G4 | G5 | G6 | implementation_status | Evidence |
|---|---|---|---|---|---|---|---|
| `template-coverage` | required | required | required | required | required | L7-carry | template catalog seeds + schema contract + L6 FN-DET-17 |
| `review-loop-closure` | optional | optional | required | required | required | L7-carry | personal workflow §2 + L6 FN-DET-18 |
| `prompt-interpretation-risk` | required | required | optional | optional | required | L7-carry | personal workflow §3 + L6 FN-DET-19 |
| `learning-forward-return` | optional | optional | optional | required | required | L7-carry | personal workflow §4 + L6 FN-DET-20 |
| `upgrade-assist-contract` | optional | optional | optional | optional | required | L7-carry | personal workflow §5 + L6 FN-DET-21 |

## 3. V-Model Pair Closure

| Left design | Right test design | design_count | test_design_count | balance_ratio | Status | HELIX personal additions |
|---|---|---|---|---|---|---|
| L1 requirements | L14 operational test | 3 | 3 | 1.00 | design-evidence pass | OT-V3-06..08 cover template freshness, learning Forward return, upgrade-assist operational closure |
| L3 requirements spec | L12 acceptance test | 6 | 6 | 1.00 | design-evidence pass | AT-V3-14..19 cover template, review, prompt escalation, learning, upgrade contract |
| L4 basic design | L9 system test | 4 | 4 | 1.00 | design-evidence pass | ST-V3-08..11 cover template flow, prompt stop, review closure, learning return |
| L5 detailed design | L8 integration test | 3 | 3 | 1.00 | design-evidence pass | IT-V3-07..09 cover template/doc coverage joins, prompt escalation joins, learning joins |
| L6 functional design | L7 unit test | 5 | 5 | 1.00 | design-evidence pass | UT-DET-17..21 cover detector-level rules |

## 4. Conditional Boundaries

This is design evidence, not runtime gate output. Runtime gate output remains incomplete until:

- actual `gate-checks.yaml` or equivalent config is updated;
- detector code is wired into `helix v3-doctor` or the equivalent registry;
- runnable tests pass for the five personal-edition rules;
- independent review findings are closed and attached to the gate evidence.
