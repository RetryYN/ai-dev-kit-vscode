# SLO/SLI: PLAN-013

## SLO

- SLO-1: `helix code build` succeeds for tracked source markers.
- SLO-2: core5 coverage gate remains >=80%.
- SLO-3: seed metadata filters return deterministic results across rebuilds.

## SLI

- SLI-1: `helix code build` exit code.
- SLI-2: `summary.coverage_pct` from `helix code stats --uncovered --scope core5 --bucket coverage_eligible --json`.
- SLI-3: item count from `--bucket private_helper --seed-candidate true --json`.

## Alert Rule

- Alert if core5 coverage drops below 80%.
- Alert if private seed candidate count is not 5.
- Alert if any excluded item has `seed_candidate=true`.
