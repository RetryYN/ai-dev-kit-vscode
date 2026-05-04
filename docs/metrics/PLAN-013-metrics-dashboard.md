# Metrics Dashboard Reference: PLAN-013

PLAN-013 is a local CLI feature. Runtime monitoring is command-output based.

## Signals

| Signal | Source | Target |
|---|---|---|
| code catalog rebuild | `helix code build` exit code | 0 |
| core5 coverage | `helix code stats --scope core5 --bucket coverage_eligible` | >=80% |
| private seed count | `--bucket private_helper --seed-candidate true --json` | 5 |
| excluded seed count | `--bucket excluded` | 0 seed candidates |

## Current Snapshot

- core5 coverage: 45/56 = 80.4%
- private seed candidates: 5
- unresolved PLAN-013 findings: 0
