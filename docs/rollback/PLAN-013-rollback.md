# Rollback: PLAN-013 Code Index Eligibility Taxonomy

## Trigger

- `helix code stats` returns incorrect seed metadata.
- `helix code build` fails to rebuild JSONL or SQLite cache.
- Core5 coverage gate drops below 80%.

## Procedure

1. Revert the PLAN-013 seed metadata code changes.
2. Revert the five explicit `seed_candidate=true` marker additions in `cli/lib/skill_catalog.py`.
3. Run `./cli/helix code build` to regenerate `.helix/cache/code-catalog.jsonl` and `.helix/helix.db`.
4. Run `./cli/helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80`.
5. Run `python3 -m pytest cli/lib/tests/test_code_catalog.py -q --tb=short`.

## Data Safety

- `helix.db` v15 fields are additive and derived.
- No destructive data operation is required.
- JSONL has `.prev` backup behavior during rebuild.
