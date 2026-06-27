# HELIX V3 — Personal Edition Gate Wiring Contract

> status: L6 design contract
> scope: template/review/prompt/learning/upgrade rules and G1/G3/G4/G5/G6 placement
> upstream: [doc-workflow-rules](doc-workflow-rules.md), [detector-wiring](detector-wiring.md), [personal-edition workflows](personal-edition-workflows.md)

## 1. Rule Inventory

| Rule id | Source kind | Hardness | Inputs | Emits finding when |
|---|---|---|---|---|
| `template-coverage` | db_projection | hard | `template_catalog`, `doc_coverage`, `artifact_registry` | required doc kind, section, or pair test kind is missing |
| `review-loop-closure` | db_projection | hard | `review_evidence_registry`, `findings`, `test_results` | viewpoint evidence missing, worker=reviewer, test-before-review violated, critical/high unresolved |
| `prompt-interpretation-risk` | db_projection | hard | `prompt_interpretations`, `findings`, `guardrail_decisions` | conflict/escalation remains unresolved before PLAN execution |
| `learning-forward-return` | db_projection | hard | `learning_candidates`, `trace_edges`, `plan_registry` | candidate lacks both `forward_return` and `discard_reason` |
| `upgrade-assist-contract` | hybrid | hard | `drive_runs`, `plan_registry`, `trace_edges`, PLAN files | version_delta/impact/rollback/staged_gate/forward_return is missing |

All five rules follow the C3 pattern:

```python
analyze_<rule>(input) -> Result
load_<rule>_input(repo_root, db) -> Input
<rule>_messages(result) -> list[Finding]
```

## 2. Gate Placement

| Gate | Added personal-edition checks | Rationale |
|---|---|---|
| G1 | `prompt-interpretation-risk`, `template-coverage` | Requirements cannot freeze while prompt scope or required requirement docs are ambiguous. |
| G3 | `template-coverage`, `prompt-interpretation-risk` | Acceptance criteria and paired test design must exist before implementation planning. |
| G4 | `template-coverage`, `review-loop-closure` | Basic design must have required architecture/design docs and multi-view review closure. |
| G5 | `template-coverage`, `review-loop-closure`, `learning-forward-return` | Detailed/internal design must close doc coverage and route learned gaps before integration design. |
| G6 | `template-coverage`, `review-loop-closure`, `prompt-interpretation-risk`, `learning-forward-return`, `upgrade-assist-contract` | Functional design must close function/test grain and block unsafe auto-run or upgrade contracts before L7. |

## 3. Rule To V-Model Pair

| Rule | Left-side design layer | Right-side test layer | Closure proof |
|---|---|---|---|
| `template-coverage` | L1/L3/L4/L5/L6 | L14/L12/L9/L8/L7 | doc_coverage includes pair_test_kind and artifact exists or waiver |
| `review-loop-closure` | L3/L4/L5/L6 | L12/L9/L8/L7 | review evidence after relevant test/design check |
| `prompt-interpretation-risk` | L1/L3/L4/L5/L6 | L14/L12/L9/L8/L7 | prompt viewpoints resolved before PLAN/gate transition |
| `learning-forward-return` | L1-L6 depending on candidate | matching right-side layer | candidate promoted to Forward or discarded with reason |
| `upgrade-assist-contract` | L4-L9, optionally L1/L3 | L9/L8/L7/L12 | staged gate and rollback evidence exists |

## 4. Gate-Checks YAML Shape

The runtime `gate-checks.yaml` equivalent must contain entries equivalent to:

```yaml
G1:
  required:
    - prompt-interpretation-risk
    - template-coverage
G3:
  required:
    - template-coverage
    - prompt-interpretation-risk
G4:
  required:
    - template-coverage
    - review-loop-closure
G5:
  required:
    - template-coverage
    - review-loop-closure
    - learning-forward-return
G6:
  required:
    - template-coverage
    - review-loop-closure
    - prompt-interpretation-risk
    - learning-forward-return
    - upgrade-assist-contract
```

This document is the design contract. L7 implementation must update the actual runtime config and tests.

## 5. Failure Fixtures Required For L7

| Rule | Red fixture | Green fixture |
|---|---|---|
| `template-coverage` | L3 subject lacks acceptance test design coverage | matching artifact and doc_coverage row exists |
| `review-loop-closure` | security critical unresolved or worker=reviewer | independent evidence and closure exists |
| `prompt-interpretation-risk` | prompt has PII/auth/prod signal and no approval | guardrail decision blocks or approval evidence exists |
| `learning-forward-return` | candidate has neither forward_return nor discard_reason | one of them exists |
| `upgrade-assist-contract` | PLAN lacks rollback_condition | all required fields exist |
