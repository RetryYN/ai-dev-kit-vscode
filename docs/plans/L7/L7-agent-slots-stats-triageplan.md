---
plan_id: L7-agent-slots-stats-triageplan
title: "L7-agent-slots-stats-triageplan: agent_slots TestStatsAggregation pytest failure triage"
kind: troubleshoot
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: QA
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: cli/lib/agent_slots.py
pairs_test_design: cli/lib/tests/test_agent_slots_integration.py
is_reference: false
agent_slots:
  - role: qa
    slot_label: "QA - reproduce pytest failures, inspect stats aggregation contract, judge quality gate"
  - role: se
    slot_label: "SE - follow-up implementation or test fix owner"
  - role: tl
    slot_label: "TL - follow-up contract judgment for stats time-window semantics"
generates:
  - artifact_path: docs/plans/L7/L7-agent-slots-stats-triageplan.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-test-failures-triageplan.md
    - docs/plans/L7/L7-pmo-role-consistency-fixplan.md
  blocks: []
related_docs:
  - cli/lib/agent_slots.py
  - cli/lib/tests/test_agent_slots_integration.py
  - cli/lib/helix_db.py
---

# L7-agent-slots-stats-triageplan: agent_slots TestStatsAggregation pytest failure triage

## §1 Scope

This PLAN records QA triage for the four existing pytest failures observed around W15-A commit `d22271a`:

- `cli/lib/tests/test_agent_slots_integration.py::TestStatsAggregation::*`
- implementation fix: out of scope
- PLAN status transition: `draft` investigation target -> `completed` after evidence and root cause were recorded

The failure is unrelated to the current 9 mode CLI, route_engine 4 mode connection, triage cleanup, or PMO role consistency work. The affected contract is `agent_slots.get_stats(days=7, by=...)` over the `agent_slots` SQLite table.

## §2 Required Code / Schema Read

| Artifact | Finding |
|---|---|
| `cli/lib/tests/test_agent_slots_integration.py` | `_seed_stats_dataset()` inserts four rows with fixed `fired_at` values around `2026-05-17 11:05:00` to `2026-05-17 11:50:00`. `TestStatsAggregation` calls `agent_slots.get_stats(days=7, by=...)` without patching SQLite `datetime('now')`. |
| `cli/lib/agent_slots.py` | `get_stats()` filters with `WHERE fired_at >= datetime('now', ?)` and parameter `-7 days`. It computes running durations with `COALESCE(released_at, datetime('now'))`. |
| `cli/lib/agent_slots_stats.py` | File does not exist in this checkout. Stats logic is in `cli/lib/agent_slots.py`. |
| `cli/lib/helix_db.py` | `agent_slots` schema stores `fired_at TEXT NOT NULL DEFAULT (datetime('now'))`, `released_at TEXT`, and status enum `running/completed/failed/cancelled`; indexes include `idx_agent_slots_fired_at`. |

## §3 Pytest Failure Evidence

Command:

```bash
python3 -m pytest cli/lib/tests/test_agent_slots_integration.py::TestStatsAggregation -v --tb=short
```

Result: `4 failed in 4.63s`.

| # | test_name | error message | root cause estimate |
|---:|---|---|---|
| 1 | `test_i_stat_001_by_hour_aggregates_total_and_peak_parallel` | `assert len(rows) == 1` failed because `len([]) == 0` at `test_agent_slots_integration.py:450` | Common time-window drift. Seed rows are fixed to `2026-05-17 11:*`, while `get_stats(days=7)` uses real SQLite `datetime('now', '-7 days')`; on `2026-05-25 JST` / `2026-05-24 UTC`, the 7-day cutoff is after the seed rows, so the base CTE is empty. |
| 2 | `test_i_stat_002_by_role_groups_none_bucket` | `KeyError: 'se'` at `test_agent_slots_integration.py:471` | Same empty result set. Role groups are absent because all seeded rows were filtered out before grouping. |
| 3 | `test_i_stat_003_by_plan_id_groups_plan_specific_rows` | `KeyError: 'PLAN-078'` at `test_agent_slots_integration.py:488` | Same empty result set. Plan groups are absent because the `WHERE fired_at >= datetime('now', '-7 days')` predicate excludes all four fixed seed rows. |
| 4 | `test_i_stat_004_by_agent_kind_groups_codex_and_subagent` | `KeyError: 'codex'` at `test_agent_slots_integration.py:503` | Same empty result set. Agent-kind groups are absent because the date window excludes the fixture rows before aggregation. |

## §4 Root Cause

Primary root cause:

1. The integration test uses a calendar-fixed dataset (`2026-05-17 11:*`) but the production stats query uses wall-clock `datetime('now')`. Once the real clock moves beyond the fixture's 7-day window, every stats grouping test becomes deterministically failing.

Secondary contributing causes:

2. `fresh_db_with_automation_runs` provides `frozen_now = 2026-05-17 12:00:00`, and stale tests explicitly call `_patch_sqlite_now(...)`, but `TestStatsAggregation` does not apply that patch before calling `get_stats()`.
3. `get_stats()` does not accept an injectable `now` or as-of parameter, so tests must monkeypatch SQLite `datetime` or seed relative to the real current time.

## §5 Fix Direction Judgment

Recommended fix: test side first, with optional implementation hardening only if a product need exists.

| Option | Judgment | Rationale |
|---|---|---|
| Test-side fix | Primary | Apply `_patch_sqlite_now(monkeypatch, fresh_db_with_automation_runs["frozen_now"])` in the four stats tests, or seed rows relative to real `datetime('now')`. This preserves the current production contract and makes the integration tests deterministic. |
| Implementation-side fix | Optional / not required for this PLAN | Add `now` / `as_of` injection only if CLI stats needs reproducible historical reports. That is a contract extension and should be handled in a separate implementation PLAN. |
| Both | Not recommended for the immediate bug | The observed failures can be resolved by deterministic test time control alone. Changing production query semantics is unnecessary for this existing-fail triage. |

Estimated follow-up files:

- primary: `cli/lib/tests/test_agent_slots_integration.py`
- optional: `cli/lib/agent_slots.py` if a future PLAN chooses to expose `as_of` semantics

## §6 Quality Gate Judgment

| Gate / Layer | Result | Evidence |
|---|---|---|
| L6 verification | fail for `TestStatsAggregation` only | 4/4 target tests fail reproducibly with empty aggregation rows. |
| G4 / G6 quality gate | changes_required | Existing unrelated failure is documented; implementation fix is intentionally out of scope for this PLAN. |
| Test quality level | T3 for existing coverage intent, temporarily degraded to T2 effective reliability | The tests cover hour/role/plan/agent_kind grouping and status counts, but lack deterministic time control. |
| Undetected risk | medium | Peak parallel and running-duration calculations may still need explicit assertions around the patched current time after the test fix. |

## §7 Verification Log

| Command | Result |
|---|---|
| `helix code find agent_slots` | Local fallback returned `agent_slots.get_stats` and related symbols; internal recommender Codex could not start in read-only session due `Read-only file system`. |
| `python3 -m pytest cli/lib/tests/test_agent_slots_integration.py::TestStatsAggregation -v --tb=short` | FAIL, 4/4 target failures reproduced. |
| `rg -n "get_stats|datetime\\('now'\\)|_patch_sqlite_now|_seed_stats_dataset|AGENT_SLOTS_SCHEMA_V28" cli/lib/tests/test_agent_slots_integration.py cli/lib/agent_slots.py cli/lib/helix_db.py` | Confirms test fixed seed, missing stats time patch, production wall-clock filter, and schema date fields. |

## §8 Acceptance

- [x] Four failing tests recorded with `test_name`, error message, and root cause estimate.
- [x] Root cause candidates recorded and common cause identified.
- [x] Fix direction judged: test-side primary, implementation-side optional.
- [x] PLAN created with `kind: troubleshoot`, `layer: L7`, `drive: be`, `status: completed`.
- [x] Implementation fix left out of scope.
