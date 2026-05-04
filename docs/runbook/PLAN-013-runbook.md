# Runbook: PLAN-013 Code Index Eligibility Taxonomy

## Scope

Local CLI release for code index taxonomy and seed metadata behavior.

## Preflight

1. Run `python3 -m pytest cli/lib/tests/ -q --tb=short`.
2. Run `./cli/helix test --no-pytest --bats-only`.
3. Run `./cli/helix code build`.
4. Run `./cli/helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80`.

## Smoke Test

1. `./cli/helix code stats --uncovered --bucket private_helper --seed-candidate true --json`
2. Confirm only explicitly marked PLAN-011 private seeds are returned.
3. `./cli/helix code stats --uncovered --bucket excluded`
4. Confirm `setup.sh`, `skills/agent-skills/hooks/*.sh`, and `verify/*.sh` entries are `seed_candidate=false`.

## Operational Notes

- No external service is required.
- No production credential is read.
- `helix.db` is a derived local cache and can be rebuilt from tracked sources.
