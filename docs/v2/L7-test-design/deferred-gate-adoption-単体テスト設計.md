---
doc_id: L7-TEST-DESIGN-DEFERRED-GATE-ADOPTION
title: "deferred gate adoption queue 単体テスト設計"
status: draft
layer: L7
pairs_design: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
pairs_with: process-roadmap
implementation_status: implemented-contract
owner: TL
created: 2026-06-09
---

# deferred gate adoption queue 単体テスト設計

## 1. 目的

本書は、`helix harness feedback-loop` / `helix doctor check_vg_overview` が出す deferred gate adoption queue を、採用完了ではなく採用待ち evidence として扱うためのテスト設計である。

対象は L6 focus clean 後に残る full-flow carry である。G8 / G9 / G12 / G14 の gate 本体は本書では実装しない。gate / detector 本体変更、DB schema migration、自動適用は別 PLAN + TL 確認で扱う。

`DGA-UT-*` は deferred gate adoption 専用テスト ID である。`g7_subcheck` は `UT-*` を実装済み L7 inventory として読むため、本テスト設計は `DGA-UT-*` のまま管理し、G7 UT inventory へ混入させない。

## 2. Scope

| Scope | 対象 | 判定 |
|---|---|---|
| VG-overview default | L6 focus clean | `overall_clean=true` だが `full_flow_execution.clean=false` を維持 |
| VG-overview strict | L0-L14 full-flow audit | `overall_clean=false`, deferred 4件 |
| feedback-loop JSON | route / learning / PLAN / PR candidate | candidate を生成し、`schema_migration=false`, `auto_apply=false`, `writes_detector_or_gate=false` |
| feedback-loop text | human-readable output | G8/G9/G12/G14 と L2-L10 waiver を表示 |
| HELIX DB observability | events / metrics / feedback | snapshot payload, metric counts, missing feedback auto-register を append |
| adoption boundary | PLAN / PR / gate evidence | candidate 生成だけでは goal complete にしない |

## 3. Deferred Pair Contract

| Pair | Gate | Required next_action | Adoption target |
|---|---|---|---|
| L5-L8 | G8 | implement G8 integration-test execution gate | L8 結合テスト execution gate / L5 詳細設計↔結合テスト設計 closure |
| L4-L9 | G9 | implement G9 system-test execution gate | L9 総合テスト execution gate / L4 基本設計↔総合テスト設計 closure |
| L3-L12 | G12 | implement G12 acceptance-test execution gate | L12 受入テスト execution gate / L3 要件定義↔受入テスト設計 closure |
| L1-L14 | G14 | implement G14 operational-learning execution gate | L14 運用学習 / 運用改善 execution gate / L1 要求定義↔運用テスト設計 closure |

## 4. Unit Test Matrix

| Planned Test ID | Name | Fixture / command | Expected |
|---|---|---|---|
| DGA-UT-01 | default L6 focus is not full-flow completion | `helix doctor check_vg_overview --json` | `overall_clean=true`, `full_flow_execution.enforced=false`, deferred 4件 |
| DGA-UT-02 | strict full-flow keeps right-arm carry | `helix doctor check_vg_overview --strict-full-flow --json` | `overall_clean=false`, `enforced=true`, pairs=`L5-L8:G8`, `L4-L9:G9`, `L3-L12:G12`, `L1-L14:G14` |
| DGA-UT-03 | feedback-loop JSON surfaces adoption candidates | `helix harness feedback-loop --json --days 30` | `vg_overview.deferred_count=4`, learning kind `full_flow_deferred_execution_gate`, PR source `vg_overview:full_flow_deferred_execution_gate` |
| DGA-UT-04 | feedback-loop text is operator-readable | `helix harness feedback-loop --days 1` | G8/G9/G12/G14 next_action と L2-L10 `ui_absent` waiver を表示 |
| DGA-UT-05 | HELIX DB snapshot preserves carry evidence | isolated DB feedback-loop run | `events.data_json.vg_overview.deferred_pairs` と metrics `full_flow_deferred_gates=4` を append |
| DGA-UT-06 | safety flags prevent auto-adoption | feedback-loop JSON and DB snapshot | `schema_migration=false`, `auto_apply=false`, `writes_detector_or_gate=false` |
| DGA-UT-07 | source categories cannot silently disappear | feedback-loop JSON | PR source keys include automation, feedback, observability, verify, hook, harness, VG deferred, and VG waiver categories |
| DGA-UT-08 | adoption readiness is explicit | test-design / roadmap contract | candidate, PLAN materialization, gate implementation, CI enforcement, and feedback closure are separate states |
| DGA-UT-09 | deferred pairs cannot be counted as closed gates | strict VG-overview / completion guard | G8/G9/G12/G14 remain adoption_required until execution gate implementation and pass evidence exist |
| DGA-UT-10 | adoption handoff remains non-destructive | feedback-loop JSON / DB snapshot | readiness evidence can be registered, but detector/gate files and DB schema are not modified automatically |

## 5. Acceptance Surfaces

| Surface | Acceptance |
|---|---|
| pytest contract | `cli/lib/tests/test_helix_l0_l14_flow_contract.py` pins L6 focus boundary, strict full-flow deferred pairs, roadmap backlog, and Web evidence |
| doctor Bats | `cli/tests/helix-doctor-json.bats` pins requirement_drift exact counts and deferred G8/G9/G12/G14 pairs |
| feedback-loop Bats | `cli/tests/test-helix-harness-feedback-loop.bats` pins JSON, text, DB payload, metrics, source keys, and safety flags |
| roadmap | `docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md` keeps deferred gate adoption queue and additional discovered improvement backlog as採用待ち evidence |

## 6. Adoption Readiness Checklist

Deferred gate adoption は、以下の state を分けて扱う。前段 state が存在しても後段 state を満たしたとは見なさない。

| State | Required evidence | Completion effect |
|---|---|---|
| candidate_generated | `helix harness feedback-loop --json` の `pr_candidates` / `plan_candidates` に G8/G9/G12/G14 が出る | 採用候補。goal complete ではない |
| plan_materialized | G8/G9/G12/G14 ごとの PLAN または task-plan が存在し、対象ファイル・受入条件・rollback が明示される | 実装着手可能性の証跡 |
| gate_implemented | execution gate 本体と regression test が実装され、`writes_detector_or_gate=false` の候補状態を脱する | gate 採用済み候補 |
| gate_passed | G8/G9/G12/G14 が実測で pass し、`execution_gate_not_implemented` が消える | pair closure 証跡 |
| ci_enforced | `helix doctor --gate` / `G-vg-overview` または同等 CI surface が strict full-flow を fail-close で見る | 自動 gate surface 証跡 |
| feedback_closed | HELIX DB events / metrics / feedback に adoption result が記録され、再発検出へ戻る | 改善 loop closure 証跡 |

## 7. Verification Commands

```bash
python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q
bats cli/tests/helix-doctor-json.bats
bats cli/tests/test-helix-harness-feedback-loop.bats
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix harness feedback-loop --json --days 30
```

## 8. Non-goals

- G8 / G9 / G12 / G14 gate 本体の実装は行わない。
- DB schema migration は行わない。
- `plan_candidates` / `pr_candidates` を自動適用しない。
- `overall_clean=true` の L6 focus 判定を goal complete と見なさない。
