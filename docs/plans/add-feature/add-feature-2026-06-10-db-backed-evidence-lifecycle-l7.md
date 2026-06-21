---
plan_id: add-feature-2026-06-10-db-backed-evidence-lifecycle-l7
title: "Action(add-feature): DB-backed evidence lifecycle L7 単体テスト設計・実装接続"
plan_scope: action
workflow: add-feature
kind: add-impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
forward_return: "L6 DBEV-FN-01..08 design -> approved L7 test-first implementation (DBEV-UT-*) -> unit execution evidence -> DB evidence lifecycle closure evidence (L6↔L7 G6/G7 pending gate evidence に帰属)."
drive: be
status: draft
tl_review: approve  # draft boundary ticket の push 承認のみ (TL L1-L6 review 2026-06-13: 境界妥当・prior L1-L6 evidence 有り・design_substitute=0)。L7 実装承認ではない (status=draft 維持、approval_required_before_* 参照)
created: 2026-06-10
owner: TL
design_change_class: contract_extension
current_task_scope: feature_ticket_only
approval_required_before_l7_work: true
approval_boundary: "This PLAN is only a ticket. L7 artifacts and implementation connection are generated only after this add-feature PLAN is explicitly approved."
generates:
  - artifact_path: docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md
    artifact_type: design_doc
  - artifact_path: cli/lib/tests/test_helix_l0_l14_flow_contract.py
    artifact_type: test
  - artifact_path: cli/tests/test-helix-l0-l14-flow-contract.bats
    artifact_type: test
dependencies:
  parent: docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  requires:
    - docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md
    - docs/v2/L5-detailed-design/db-backed-evidence-lifecycle-詳細設計.md
    - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
  blocks: []
related_docs:
  - docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml
  - docs/v2/L7-test-design/goal-completion-audit.yaml
unlock_conditions:
  - db_write
  - document_auto_registration
  - feedback_loop
  - recurrence_closure
---

# DB-backed evidence lifecycle L7 単体テスト設計・実装接続

## 1. 目的

L4-L6 で補正した DB-backed evidence lifecycle を、L7 の単体テスト設計と実装接続へ進めるための add-feature 起票である。現在フェーズでは L7 成果物を作成せず、本 PLAN を次工程の入口にする。

この PLAN は L7 作業の承認要求であり、現在タスクで L7 成果物を生成した証跡ではない。`generates` に列挙した成果物は、本 PLAN が明示承認された後にだけ作成対象になる。

Draft only. This is a feature ticket only and not completion evidence for L7 implementation, HELIX DB write adoption, feedback closure, or strict full-flow completion.

## 2. Scope

### In

- L6 `DBEV-FN-01..08` に対応する `DBEV-UT-*` 単体テスト設計を作成する。
- L1-L6 で定義済みの document projection contracts を HELIX DB / registry 書き込みへ接続する。
- `document_auto_registration` を、L6 function spec / glossary / design trace / unit-test viewpoint / audit manifest の登録対象として実装する。
- feedback loop snapshot / detector candidate / recurrence closure の永続化境界を実装する。
- `candidate_generated`、`plan_materialized`、`verification_recorded`、`gate_projected`、`recurrence_closed` の状態遷移をテストで固定する。
- candidate 生成を closure と誤認しない契約を pytest / Bats で固定する。
- L6 focus clean と full-flow completion を分離する契約を固定する。
- **F2 実行証跡（2026-06-21 design-review 補正、L4 §7 / L5 §6 / L6 §3.1 で設計確定）**: `exec_status`（`exec_pass`/`exec_fail`/`exec_skipped`/`exec_missing_evidence`）の分離と、`exec_skipped`/`exec_missing_evidence` を pass に算入しない契約を pytest / Bats で固定する。`is_genuine_exec_evidence`（`artifact_sha256` 実体一致 ∧ `exit_code=0`）の判定を実装する。
- **F2 gate verification 置換**: push gate / CI の `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` skip を、変更 pair の genuine artifact 参照判定へ置換し、`g7_subcheck` の skip-time exec_pass 計上を修正する（skip ≠ pass）。CI 速度は別 job で artifact を生成して維持する。

### Out

- DB schema migration。
- candidate の auto-apply。
- G8/G9/G12/G14 の right-arm 実走 gate 実装。
- CI / infrastructure 変更。

## 2.1 Unlock Conditions

This ticket can only unlock full-goal DB evidence after all of the following are implemented and verified after explicit approval:

- `db_write`: approved HELIX DB / registry write path exists and reports deterministic success / failure.
- `document_auto_registration`: L6 function specs, glossary terms, design traces, unit-test viewpoints, and audit manifests are projected from documents into the approved registry targets.
- `feedback_loop`: detector / trouble candidates are persisted as feedback candidates without being counted as closure.
- `recurrence_closure`: recurrence is closed only after gate projection or monitored owner acceptance evidence exists.

These unlock conditions are routes for later work. They are not satisfied by this draft ticket.

## 3. Acceptance

- `docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md` が `DBEV-UT-*` を定義する。
- document projection contract rows from `docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml` are covered by L7 tests before implementation.
- `DBEV-UT-*` は既存 `UT-*` inventory へ混入しない。
- The implementation distinguishes `candidate_generated`, `plan_materialized`, `verification_recorded`, `gate_projected`, and `recurrence_closed`.
- No candidate, projection, or draft ticket is counted as full-goal completion evidence before closure criteria are met.
- **F2**: `exec_skipped` / `exec_missing_evidence` は `verification_recorded` へ遷移せず pass に算入されない。`test_execution_pass` は genuine `exec_pass`（`artifact_sha256` 一致 ∧ `exit_code=0`）のみで真。`g7_subcheck` の skip-time exec_pass 計上が修正され、`SKIP_EXEC_TESTS` 時に exec_pass を詐称しない。
- `python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q` が pass。
- `bats cli/tests/test-helix-l0-l14-flow-contract.bats` が pass。
- `helix doctor check_requirement_drift --json` が L6 focus clean を維持する。

## 4. Safety

- `schema_migration=false`
- `destructive_data_operation=false`
- `auto_apply=false`
- `external_api_or_infrastructure_change=false`
- L7 着手は本 PLAN の承認後に限る。
- 現在タスクでは `docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md` を作成しない。
