---
plan_id: L7-pmo-role-consistency-fixplan
title: "L7-pmo-role-consistency-fixplan: helix doctor PMO role consistency bats failure triage"
kind: troubleshoot
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: QA
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: cli/helix-doctor
pairs_test_design: cli/tests/test-helix-doctor-pmo.bats
is_reference: false
agent_slots:
  - role: qa
    slot_label: "QA - reproduce bats failure, inspect doctor role consistency, judge quality gate"
  - role: se
    slot_label: "SE - follow-up implementation owner if doctor logic is fixed"
  - role: pmo-sonnet
    slot_label: "PMO - follow-up role policy consistency review"
generates:
  - artifact_path: docs/plans/L7/L7-pmo-role-consistency-fixplan.md
    artifact_type: design_doc
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: test_code
dependencies:
  parent: docs/plans/L7/L7-test-failures-triageplan.md
  requires:
    - docs/plans/L7/L7-bats-directory-sweep-compatplan.md
  blocks: []
related_docs:
  - cli/helix-doctor
  - cli/tests/test-helix-doctor-pmo.bats
  - cli/config/models.yaml
  - cli/roles/pmo-sonnet.conf
  - cli/roles/pmo-haiku.conf
  - .claude/agents/pmo-sonnet.md
  - .claude/agents/pmo-haiku.md
---

# L7-pmo-role-consistency-fixplan: helix doctor PMO role consistency bats failure triage

## §1 Scope

This PLAN records investigation of the W13-A residual bats failure:

- failing test: `cli/tests/test-helix-doctor-pmo.bats`
- test name: `helix doctor shows pmo role consistency`
- observed initial output in this QA session: `not ok 1 - helix doctor shows pmo role consistency`
- implementation fix: out of scope for this PLAN

The investigation completed in this PLAN; any implementation or test change must be handled by a follow-up L7 PLAN if the failure becomes reproducible again.

## §2 Failure Detail

| Item | Evidence |
|---|---|
| Failing file | `cli/tests/test-helix-doctor-pmo.bats` |
| Failing assertion | line 20 expects doctor text output to contain `✓ pmo role consistency` |
| Initial reproduction | `bats cli/tests/test-helix-doctor-pmo.bats` returned status 1 with `not ok 1 - helix doctor shows pmo role consistency` |
| Current reproduction | rerun returned `ok 1 - helix doctor shows pmo role consistency` |
| Related sweep context | W13-A reported this as a residual failure after bats-lite directory sweep compatibility work |

The current checkout is not in a persistently failing state for this test. A diagnostic copy of the same bats test printed `STATUS=0` and doctor output containing `✓ pmo role consistency`, then the original test also passed on rerun.

## §3 Code / Test Findings

### Doctor logic

`cli/helix-doctor` implements `check_role_config_consistency` directly. `cli/lib/role_validator.py` does not exist in the current tree, so the relevant module is `cli/helix-doctor`.

Key behavior:

- `cli/helix-doctor` lines 327-328 read SoT from `${HELIX_HOME}/cli/config/models.yaml` and role confs from `${HELIX_HOME}/cli/roles`.
- Lines 364-416 treat every `pmo-*` role as a PMO role.
- Lines 365-388 compare `claude_model`, `claude_thinking`, `claude_permission_mode`, and `claude_disallowed_tools` against `roles.<role>` / `role_metadata.<role>.*`.
- Lines 393-413 mirror `codex_*` fields when those fields are present in conf.
- Lines 442-447 print `✓ pmo role consistency` only when `pmo_mismatch=0`; otherwise they print `△ pmo role consistency`.

### Source-of-truth state

`cli/config/models.yaml` defines the PMO role models and metadata for `pmo-sonnet`, `pmo-haiku`, `pmo-tech-*`, `pmo-helix-*`, and `pmo-project-*`. The sampled PMO conf files match the current YAML values:

- `cli/roles/pmo-sonnet.conf`: `claude_model=claude-sonnet-4-6`, `claude_thinking=medium`, `claude_permission_mode=plan`, disallowed tools mirrored.
- `cli/roles/pmo-haiku.conf`: `claude_model=claude-haiku-4-5-20251001`, `claude_thinking=low`, `claude_permission_mode=acceptEdits`, allow paths mirrored.

### Claude agent definitions

`.claude/agents/pmo-sonnet.md` and `.claude/agents/pmo-haiku.md` frontmatter currently match model/effort expectations:

- `pmo-sonnet`: `model: claude-sonnet-4-6`, `effort: medium`
- `pmo-haiku`: `model: claude-haiku-4-5-20251001`, `effort: low`

However, the doctor PMO role consistency check does not currently validate `.claude/agents/*.md` frontmatter. It validates `cli/roles/*.conf` against `cli/config/models.yaml`.

## §4 Root Cause Hypotheses

| # | Hypothesis | Confidence | Evidence |
|---:|---|---:|---|
| 1 | Transient bats/sweep state rather than persistent contract failure | medium | Initial direct run failed once; diagnostic run and rerun passed with `✓ pmo role consistency`; `helix doctor` reports `25 pass, 0 fail, 94 warn`. |
| 2 | Test assertion is too coarse and gives no mismatch diagnostic | high | The bats file only checks status 0 and substring presence. When it fails, it does not print doctor output or PMO mismatch warnings. |
| 3 | Doctor check naming is broader than the implemented logic | medium | Task expected `.claude/agents` consistency review, but `check_role_config_consistency` only compares `cli/roles/*.conf` with `cli/config/models.yaml`. Agent frontmatter drift would not be caught by this specific pass/fail. |

## §5 Fix Direction

Decision: both test-side and implementation-side follow-up are recommended, but no implementation change is made in this PLAN.

| Area | Direction | Rationale |
|---|---|---|
| Test side | Add diagnostics to `cli/tests/test-helix-doctor-pmo.bats` so failures print status and role warning lines | Required because the current failure output is not actionable. |
| Implementation side | Consider extracting PMO role validation into `cli/lib/role_validator.py` or an equivalent module with unit tests | Current logic is embedded in bash and difficult to test at mismatch granularity. |
| Contract side | Decide whether PMO consistency should include `.claude/agents` frontmatter | Current check name suggests broader PMO consistency, but implementation only checks YAML/conf mirrors. |

Estimated follow-up files:

- `cli/tests/test-helix-doctor-pmo.bats`
- `cli/helix-doctor`
- optional new module: `cli/lib/role_validator.py`
- optional unit tests: `cli/lib/tests/test_role_validator.py`

## §6 Quality / Gate Judgment

| Gate | Decision | Evidence |
|---|---|---|
| G4 | pass for investigation artifact | PLAN creation only; no production code or test contract changed. |
| G6 | pass with residual risk | Current targeted bats passes, doctor remains `25 pass / 0 fail`; residual risk is non-reproducible sweep-only failure. |

Quality level: T3.

- Density: T3 - targeted bats, doctor, source files, and role definitions inspected.
- Depth: T3 - root cause narrowed to transient/test-diagnostic/contract-boundary hypotheses.
- Breadth: T3 - bash doctor, YAML SoT, role confs, and Claude agent frontmatter covered.
- Accuracy: T3 - persistent failure not reproduced; conclusion is hypothesis-based.
- Maintainability: T4 - follow-up scope is narrow and separates test diagnostics from validator refactor.

## §7 Verification Evidence

| Command | Result |
|---|---|
| `bats cli/tests/test-helix-doctor-pmo.bats` | initial run: failed once; rerun: `1..1`, PASS |
| `bats cli/tests/test-helix-doctor-pmo.bats cli/tests/helix-doctor-json.bats` | `1..6`, PASS |
| `helix doctor` | `25 pass, 0 fail, 94 warn`; includes `✓ pmo role consistency` |
| `helix code find "pmo role consistency"` | attempted; recommender read-only Codex session failed to initialize, local fallback returned no direct output |

## §8 Acceptance

- [x] Failure file and test name identified.
- [x] Failure content recorded from initial reproduction.
- [x] Doctor PMO role consistency logic inspected.
- [x] `cli/lib/role_validator.py` absence confirmed.
- [x] `cli/config/models.yaml`, PMO role confs, and `.claude/agents` sampled.
- [x] Fix direction decided: test diagnostics first, then optional validator extraction / agent-frontmatter contract decision.
- [x] `helix doctor` remains `25 pass / 0 fail`.
- [x] Implementation fix deferred to follow-up PLAN.

## §9 Residual Risk

- The W13-A sweep failure may depend on bats-lite ordering, hidden temporary files, or a transient workspace state not reproduced in this focused run.
- Without diagnostic output in the bats test, future failures will still require manual doctor reruns to identify actual mismatches.
- If `.claude/agents` frontmatter is intended to be part of PMO role consistency, the current doctor pass is incomplete and should become a separate explicit check.
