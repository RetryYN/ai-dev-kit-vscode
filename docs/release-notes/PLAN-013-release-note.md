# Release Note: PLAN-013 Code Index Eligibility Taxonomy

Date: 2026-05-04

## Changes

- Fixed seed metadata defaults:
  - `coverage_eligible`: `seed_candidate=true`
  - `private_helper`: `seed_candidate=false` unless explicitly marked
  - `excluded`: always `seed_candidate=false` and `seed_promotable=false`
- Added marker support for `seed_candidate=true|false` and `seed_promotable=true|false`.
- Marked the five PLAN-011 private seed helpers explicitly as `seed_candidate=true`.
- Restored `helix task plan/status` by fixing embedded Python f-string syntax.
- Added PLAN-013 sprint, task-plan, security review, and contract/migration/debt evidence.

## Verification

- `python3 -m pytest cli/lib/tests/ -q --tb=short`: 696 passed
- `./cli/helix test --no-pytest --bats-only`: 237 Bats passed + 5 shell checks passed
- `./cli/helix gate G4`: PASS
- `./cli/helix gate G6`: PASS
