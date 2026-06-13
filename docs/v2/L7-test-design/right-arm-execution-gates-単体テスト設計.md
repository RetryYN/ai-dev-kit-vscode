---
doc_id: L7-TEST-DESIGN-RIGHT-ARM-EXECUTION-GATES
title: "right-arm execution gates 単体テスト設計"
status: draft
layer: L7
pairs_design: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
pairs_with: L8,L9,L12,L14
implementation_status: planned-contract
owner: TL
created: 2026-06-09
---

# right-arm execution gates 単体テスト設計

## 1. 目的

本書は、L6 focus clean 後に strict full-flow で残る G8 / G9 / G12 / G14 execution gate の実装受入条件を固定する。

現 handover では gate / detector 本体を実装しない。ここでは `plan_materialized` 後に `gate_implemented` / `gate_passed` / `ci_enforced` / `feedback_closed` へ進めるための test contract だけを定義する。

`EGA-UT-*` は right-arm execution gate adoption 専用テスト ID である。`g7_subcheck` の `UT-*` inventory、つまり G7 UT inventory へ混入させない。

## 2. Gate Acceptance Contract

| Gate | Pair | Pass condition | Must disappear |
|---|---|---|---|
| G8 | L5-L8 | 結合テスト execution evidence と L5 詳細設計↔結合テスト設計 trace closure が存在する | `L5-L8` の `execution_gate_not_implemented` |
| G9 | L4-L9 | 総合テスト execution evidence と L4 基本設計↔総合テスト設計 trace closure が存在し、`semantic_excluded_orphan=18` の根拠が維持される | `L4-L9` の `execution_gate_not_implemented` |
| G12 | L3-L12 | 受入テスト execution evidence と L3 要件定義↔受入テスト設計 closure が存在する | `L3-L12` の `execution_gate_not_implemented` |
| G14 | L1-L14 | 運用テスト / 運用学習 evidence が HELIX DB events / metrics / feedback に戻り、再発検出へ接続される | `L1-L14` の `execution_gate_not_implemented` |

## 3. Unit Test Matrix

| Planned Test ID | Name | Fixture / command | Expected |
|---|---|---|---|
| EGA-UT-01 | strict full-flow starts with four deferred gates | `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json` | `overall_clean=false`, deferred pairs are `L5-L8:G8`, `L4-L9:G9`, `L3-L12:G12`, `L1-L14:G14` |
| EGA-UT-02 | G8 closure requires integration execution evidence | simulated G8 implemented fixture | G8 disappears only when L5-L8 integration execution evidence and trace closure are both present |
| EGA-UT-03 | G9 closure preserves semantic system-test trace | simulated G9 implemented fixture | G9 disappears only when L4-L9 execution evidence exists and `semantic_excluded_orphan=18` remains justified |
| EGA-UT-04 | G12 closure requires acceptance execution evidence | simulated G12 implemented fixture | G12 disappears only when L3-L12 acceptance execution evidence exists |
| EGA-UT-05 | G14 closure writes feedback loop evidence | isolated HELIX DB fixture | G14 disappears only when events / metrics / feedback contain adoption result and operational-learning evidence |
| EGA-UT-06 | partial right-arm adoption stays fail-close | one or more gates still deferred | strict full-flow keeps `overall_clean=false` until all G8/G9/G12/G14 pass |
| EGA-UT-07 | CI surface separates L6 focus from full-flow strictness | `helix doctor --gate --json` and strict VG-overview | L6 focus can remain clean while strict full-flow reports remaining right-arm carry |
| EGA-UT-08 | rollback returns implemented gate to deferred state | regression fixture after rollback | failed or reverted gate returns to `approved_deferred` with original next_action and does not hide carry |

## 4. Implementation Handoff

| Gate | Draft PLAN | Implementation handoff |
|---|---|---|
| G8 | `PLAN-G8-INTEGRATION-EXECUTION-GATE` | Implement execution evidence reader, regression tests, and strict VG-overview removal of G8 deferred. |
| G9 | `PLAN-G9-SYSTEM-EXECUTION-GATE` | Implement system-test execution evidence reader while preserving semantic trace exclusion. |
| G12 | `PLAN-G12-ACCEPTANCE-EXECUTION-GATE` | Implement acceptance execution evidence reader and L3-L12 closure check. |
| G14 | `PLAN-G14-OPERATIONAL-LEARNING-GATE` | Implement operational learning evidence reader and HELIX DB feedback closure check. |

## 5. Verification Commands

```bash
python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q
bats cli/tests/test-helix-l0-l14-flow-contract.bats
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json
```

## 6. Non-goals

- G8 / G9 / G12 / G14 gate 本体の実装は行わない。
- strict full-flow の deferred 4件をこの文書だけで closure 扱いしない。
- DB schema migration は行わない。
- `ui_absent` waiver の L2-L10 判定は本書の対象外とする。
