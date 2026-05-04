# Security Review: PLAN-013 Code Index Eligibility Taxonomy

Date: 2026-05-04
Scope: `helix code` catalog classification, seed metadata, JSONL cache, and SQLite derived cache.

## Result

- Critical: 0
- High: 0
- Medium: 0

## Checks

- Secret handling: marker summaries still pass through `should_redact`; secret-like summaries are rejected before JSONL/DB sync.
- Injection: new marker fields are parsed as literal key/value metadata; they are not executed.
- Data integrity: `excluded` paths always force `seed_candidate=false` and `seed_promotable=false`.
- Privilege boundary: `seed_promotable=true` is effective only for `private_helper`; public and excluded symbols ignore it.
- Rollback: v15 DB fields are additive; catalog state can be rebuilt from tracked source markers with `helix code build`.

## Evidence

- `python3 -m pytest cli/lib/tests/test_code_catalog.py -q --tb=short`
- `bats cli/tests/test-helix-code.bats`
- `./cli/helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80`

## Residual Risk

- No PLAN-013 Critical/High residual risk remains.
- `seed_promotable` heuristic remains deferred and disabled by default.
