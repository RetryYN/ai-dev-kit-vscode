# HELIX Completion Memory Update

Date: 2026-05-04
Scope: PLAN-001 through PLAN-018 completion cleanup

## Summary

This repository has no checked-in `MEMORY.md`. Claude auto memory is treated as
external personal state, so repo-local completion facts are recorded here as a
shareable, non-secret memory update.

## Current Facts

- PLAN-002 through PLAN-018 are finalized and reviewed.
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
- 2026-05-05 follow-up verification passed: `python3 -m pytest cli/lib/tests/`
  783 passed, `helix test --no-pytest --bats-only` 259 Bats passed and 5 shell
  checks passed.
- 2026-05-05 T2/PLAN-017 remediation: PLAN-017 was finalized retroactively,
  and PLAN-018 was created as the retroactive source of truth for the LLM Guard
  / research guard / agent policy hardening work that had previously landed
  without a PLAN.
- 2026-05-05 final remediation verification passed: `./cli/helix test` reported
  shell 609 passed / Bats 267 passed / pytest 826 passed.

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

## LLM Guard and Context Budget

- Raw LLM CLI bypass is guarded in two layers:
  `cli/libexec/helix-pre-bash` for Claude Code Bash PreToolUse and PATH shims
  (`cli/codex`, `cli/claude`).
- `cli/lib/llm_guard.py` is the shared raw LLM command detector. It allows
  HELIX harness commands such as `helix codex --plan-only`,
  `helix codex --approved`, and `helix claude --dry-run`, and blocks
  unapproved raw Codex / Claude execution.
- `cli/helix-context` / `cli/lib/context_guard.py` provide repository-local
  context budget checks for AGENTS / CLAUDE / hook docs.
- `helix context check --json` passes with zero errors and zero warnings; the
  local raw LLM allowlist is reported as informational because Bash
  PreToolUse is configured as block-on-failure.

## PLAN-017 Coverage Closure

- `docs/plans/PLAN-017-bats-coverage-core-cli.md` was updated from initial
  assumptions to draft v1 reality: handover / gate already had meaningful
  Bats coverage, while plan / codex needed focused additions.
- Added `cli/tests/test-helix-plan.bats` for plan lifecycle contracts:
  help, empty list, draft creation, ID increment, status, finalize guard, and
  invalid ID rejection.
- Added `cli/tests/test-helix-codex.bats` for Codex harness safety contracts:
  help, required args, role validation, plan-only dry-run, execution context
  injection, missing reference docs, and require-approved guard.
- 2026-05-05 retro: PLAN-017 status is now `finalized`. The implementation
  commit happened while the plan still said `draft`; this is recorded as a
  process violation and closed by retro review, memory update, and regression
  verification.

## PLAN-018 LLM Guard Retroactive Closure

- `docs/plans/PLAN-018-llm-guard-retroactive-hardening.md` formalizes the T2
  LLM Guard work after the fact because commit `761e2d3` added a large guard
  surface without a PLAN.
- G2/G3/G4 were evaluated retroactively with `--static-only --dry-run
  --readiness-mode skip` and passed.
- The guard surface now covers raw Codex / Claude shims, Claude Bash
  PreToolUse, WebSearch / WebFetch PreToolUse, role policy, context guard,
  and merge settings canonical hook coverage.
- A regression bug was found during remediation: `helix-gate` static checks ran
  without `pipefail`, so `! rg ... | head` absence checks could false-fail.
  `cli/helix-gate` now runs static checks with `bash -o pipefail -c`.

## Remaining Non-Repo Decisions

- Applying this update to external Claude auto memory is outside the repository
  checkout and must not be treated as a HELIX implementation gap.
- PLAN-001 should not be finalized from the reconstructed fallback. Future PoC
  workflow changes should use the PoC skill or a new PLAN with complete source
  evidence.
