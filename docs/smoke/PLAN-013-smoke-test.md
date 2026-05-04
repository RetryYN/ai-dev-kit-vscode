# Smoke Test: PLAN-013

Date: 2026-05-04

## Commands

- `./cli/helix code build`
- `./cli/helix code stats --uncovered --bucket private_helper --seed-candidate true --json`
- `./cli/helix code stats --uncovered --bucket excluded`
- `./cli/helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80`

## Result

- JSONL and SQLite cache rebuild completed.
- PLAN-011 private seed helpers remain the only `private_helper` seed candidates.
- Excluded operational scripts are never seed candidates.
- Core5 coverage gate remains 45/56 = 80.4%.
