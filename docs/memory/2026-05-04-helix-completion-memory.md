# HELIX Completion Memory Update

Date: 2026-05-04
Scope: PLAN-001 through PLAN-016 completion cleanup

## Summary

This repository has no checked-in `MEMORY.md`. Claude auto memory is treated as
external personal state, so repo-local completion facts are recorded here as a
shareable, non-secret memory update.

## Current Facts

- PLAN-002 through PLAN-016 are finalized and reviewed.
- PLAN-001 remains `draft` in PLAN YAML by design because the original source
  file `/tmp/helix-plan-source-poc.txt` is unavailable.
- PLAN-001 now has a tracked fallback reference:
  `docs/plans/PLAN-001-poc-skill.md`.
- PLAN-001 is superseded by `skills/workflow/poc/SKILL.md` and is excluded
  from the completion denominator.
- Open/carried deferred findings are currently zero.
- `helix meta-phase check --json` passes with 3 patterns.
- `helix init` now installs the default `.helix/patterns/pattern.yaml`
  template, so initialized projects can run `helix meta-phase check` against
  their project-local pattern contract.
- The lightweight YAML parser supports the documented nested `all` / `any`
  `applies_when` shape used by PLAN-006.
- `helix code stats --uncovered --scope core5 --fail-under 80` passes at
  80.4 percent coverage.
- 2026-05-04 final verification passed: `python3 -m pytest cli/lib/tests/`
  706 passed, `helix test --no-pytest --bats-only` 242 Bats passed and 5 shell
  checks passed.

## Builder System

- Builder System is implemented in `cli/lib/builders/*` and exposed through
  `cli/helix-builder`.
- The current CLI registry exposes 8 builder types:
  `agent-loop`, `agent-pipeline`, `agent-skill`, `json-converter`,
  `sub-agent`, `task`, `verify-script`, and `workflow`.
- `docs/commands/builder.md` uses the implemented action vocabulary:
  `schema`, `info`, `generate`, `validate`, and `history`.
- `docs/adr/ADR-008-builder-abstraction.md` is synchronized to 8 registered
  builders.

## Auto-Thinking

- `cli/lib/effort_classifier.py` provides the task-to-effort classifier.
- `helix codex --auto-thinking --dry-run` applies the classifier and reports
  the selected reasoning effort.
- `helix skill use ... --auto-thinking` accepts the option and applies it when
  routing to a Codex role.
- Skill usage telemetry exists through `helix skill stats --json`; long-running
  operational learning remains staged rather than an active blocker.

## Remaining Non-Repo Decisions

- Applying this update to external Claude auto memory is outside the repository
  checkout and must not be treated as a HELIX implementation gap.
- PLAN-001 should not be finalized from the reconstructed fallback. Future PoC
  workflow changes should use the PoC skill or a new PLAN with complete source
  evidence.
