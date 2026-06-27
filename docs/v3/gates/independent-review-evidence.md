# HELIX V3 — Independent Review Evidence

> status: changes_required
> reviewer: `helix codex --role doc-reviewer --plan-only --read-only`
> reviewed_at: 2026-06-27 JST
> related item: G0.5 progress item #25

## 1. Command

```bash
helix codex --role doc-reviewer --plan-only --read-only \
  --task-file docs/v3/gates/independent-review-request.md \
  --timeout 300 --no-record
```

## 2. Decision

Decision: `changes_required`

No P0 blocker was reported. The reviewer stated that G0.5 `24/26 = 92.31%` matched the table and did not claim implementation completion. The reviewer also stated that item #25 can be considered independently reviewed after the P1 findings are fixed.

## 3. Findings

| Severity | Finding | Required fix |
|---|---|---|
| P1 | `implementation_status` is missing for implementation-looking claims | Add `implementation_status` to table/rule/interface claims and distinguish design contract from runtime implementation. |
| P1 | V-model same-grain closure is traced but lacks quantitative `balance_ratio >= 1.0` evidence | Add `design_count`, `test_design_count`, `balance_ratio`, and `status` to the V-model pair evidence. |
| P2 | G1-G6 `pass` wording can be misread as runtime gate pass | Change wording to `design-evidence pass` or equivalent. |
| P2 | Machine verification checks fixed progress strings instead of computing the table status | Parse the G0.5 table and compute complete/incomplete counts. |

## 4. Reviewer Verification

The reviewer ran:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_v3_personal_edition_design.py
```

Result:

```text
personal-edition-design-check: ok
```

Note: `py_compile` could not be used inside the delegated read-only sandbox because Python attempted to write `__pycache__`. The main session separately runs `py_compile` outside that sandbox.

## 5. Closure Update

P1/P2 closure was applied after this review:

- `implementation_status` was added to gate/rule evidence and all personal table column contracts.
- `balance_ratio` quantitative evidence was added to G1-G6 V-model pair closure.
- G1-G6 `pass` wording was narrowed to `design-evidence pass`.
- `scripts/check_v3_personal_edition_design.py` now parses the G0.5 status table and validates the computed complete/incomplete counts.

Closure status: #25 can be counted as complete after the local verifier passes.

## 6. Trace Limitation (honesty note)

The review was run with `--no-record`, so no rollout JSONL / session-id trace was captured. The evidence that this was a genuine independent pass (not self-attestation) is **indirect but substantive**: the delegated `doc-reviewer` role returned concrete P1/P2 findings (missing `implementation_status`, missing quantitative `balance_ratio`) that required real rework, and that rework was applied (§5) — a fabricated self-review would not have produced findings forcing changes. The remaining gap is the absence of a machine-captured rollout log. If a stronger trace is required before downstream G1-G6 reliance, re-run the review **without** `--no-record` and attach the rollout excerpt, or have a human/Opus PMO independently re-verify. Until then, #25 should be read as *design-evidence reviewed, trace-light*, not *machine-traced independent review*.
