---
doc_id: L6-FUNCTIONAL-DESIGN-DB-BACKED-EVIDENCE-LIFECYCLE
title: DB-backed evidence lifecycle 機能設計
status: draft
layer: L6
pairs_with: L7
next_feature_plan: docs/plans/add-feature/add-feature-2026-06-10-db-backed-evidence-lifecycle-l7.md
parent_design:
  - docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md
  - docs/v2/L5-detailed-design/db-backed-evidence-lifecycle-詳細設計.md
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
---

# DB-backed evidence lifecycle 機能設計

## 1. 目的

`DB-backed evidence lifecycle` は、DDD / TDD / V-model gate の自動検出結果を DB 証跡として正規化し、改善候補から closure までの状態を機械的に追えるようにする機能群である。

既存の `helix harness feedback-loop`、`VG-overview`、`requirement_drift`、`trace_symmetry`、`goal-completion-audit` を接続する設計であり、新規 schema や auto-apply は前提にしない。

## 2. 上位 Trace

| 上位要件 / 設計 | 本機能での役割 |
|---|---|
| FR-DRIFT-01 | drift / trace gap の検出元 |
| FR-GATE-01 | gate projection / fail-close の接続先 |
| FR-4ART-01 | design / test-design / code / test evidence の trace |
| L4 DB-backed evidence lifecycle | 外部的な lifecycle と安全境界 |
| L5 DB-backed evidence lifecycle | state machine と既存 DB 写像 |

## 3. 機能一覧

| FN-ID | 関数 / surface | 入力 | 出力 | 判定 |
|---|---|---|---|---|
| DBEV-FN-01 | normalize_detector_signal | detector / doctor / hook / harness finding | normalized signal dict | `source_category`, `source_signal_id`, `detector_name`, `pair`, `gate_id` を持つ |
| DBEV-FN-02 | register_evidence_event | normalized signal, payload | evidence record | 既存 `events` / `metrics` / `feedback` / `audit_log` に append できる |
| DBEV-FN-03 | generate_adoption_candidate | evidence record | route / learning / PLAN / PR candidate | `candidate_generated` 止まりで closure 扱いしない |
| DBEV-FN-04 | materialize_plan_reference | candidate, owner, allowed_files, acceptance, rollback | PLAN / task reference | `plan_materialized` に必要な管理項目を満たす |
| DBEV-FN-05 | record_verification_evidence | command result, gate result, CI/equivalent result | verification evidence | pytest / Bats / doctor / CI equivalent の実行結果を参照できる |
| DBEV-FN-06 | project_gate_status | verification evidence, original signal | gate projection | absent / closed / monitored_with_owner / deferred を分離する |
| DBEV-FN-07 | close_recurrence | candidate_id, gate evidence, recurrence observation | recurrence status | `closed` または `monitored_with_owner` のみ closure 候補 |
| DBEV-FN-08 | emit_completion_guard_summary | lifecycle states, strict full-flow status | goal audit summary | L6 focus clean と full-flow completion を混同しない |

### 3.1 実行証跡 genuine 判定の DbC（F2 — L4 §7 / L5 §6 の機能化）

`DBEV-FN-05 record_verification_evidence` を「skip を pass に数えない」genuine 判定として固定する。新規 FN-ID は増やさず（UT は L7 add-feature で deferred のため）、本関数の契約を強化する。

**DBEV-FN-05 record_verification_evidence（契約強化、F2-1〜F2-3）**

- **requires**: command / gate result が `run_id`・`commit_sha`・`target_pair`・`exit_code`・`artifact_sha256` を伴う（L4 §7 F2-1 / L5 §6.2）。
- **ensures**: 返す `exec_status` は `exec_pass | exec_fail | exec_skipped | exec_missing_evidence` のいずれか。`exec_pass` は **`exit_code=0` かつ `artifact_sha256` が実体一致**のときのみ（L5 §6.3 の genuine 条件）。
- **invariant**: `exec_skipped` / `exec_missing_evidence` のとき `verification_recorded` へ遷移させない。pair_closure の `test_execution_pass` は **genuine な `exec_pass` のみ**で真（skip / 未実行を pass に算入しない）。

**判定補助 surface `is_genuine_exec_evidence(artifact) -> bool`**

- **requires**: artifact が F2-1 の全 field を持つ。
- **ensures**: `sha256(実体) == artifact_sha256` ∧ `exit_code == 0` のときのみ true。
- **invariant**: field 不在 / sha256 不一致 / 別 commit 由来は false（fail-close。未実行・改ざんを genuine 扱いしない）。

## 4. Output Contract

```yaml
db_backed_evidence_lifecycle:
  candidate_id: string
  source_category: string
  source_signal_id: string
  detector_name: string
  pair: string
  gate_id: string
  state: detected | registered | candidate_generated | plan_materialized | implementation_adopted | verification_recorded | gate_projected | recurrence_closed
  exec_status: exec_pass | exec_fail | exec_skipped | exec_missing_evidence   # F2: skip/missing は pass 非算入
  exec_evidence:                                                              # F2-1 実行証跡 artifact (genuine 条件)
    run_id: string
    commit_sha: string
    target_pair: string
    exit_code: int
    artifact_sha256: string
    genuine: bool   # is_genuine_exec_evidence の結果 (sha256 一致 ∧ exit_code=0)
  evidence_refs: []
  safety:
    schema_migration: false
    destructive_data_operation: false
    auto_apply: false
    production_db_operation: false
  completion:
    l6_focus_clean_is_full_goal_completion: false
    recurrence_status: open | closed | monitored_with_owner
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| candidate のみ | `goal_complete_allowed=false` |
| DB snapshot のみ | `goal_complete_allowed=false` |
| PLAN materialized のみ | `goal_complete_allowed=false` |
| verification なし | `gate_projected` へ進めない |
| `exec_status` が `exec_skipped` / `exec_missing_evidence`（F2） | `verification_recorded` へ進めない（skip を pass に数えない） |
| `exec_evidence.genuine=false`（F2） | `test_execution_pass=false`、gate fail-close |
| gate projection なし | `recurrence_closed` へ進めない |
| recurrence_status が `closed` / `monitored_with_owner` 以外 | closure 不可 |
| strict full-flow `deferred_count > 0` | full goal completion 不可 |

## 6. L7 起票

本タスクでは L7 単体テスト設計を作成しない。L7 で `DBEV-UT-*` を定義し、既存 `UT-*` inventory へ混入させない契約を固定する作業は `docs/plans/add-feature/add-feature-2026-06-10-db-backed-evidence-lifecycle-l7.md` で feature 起票する。
