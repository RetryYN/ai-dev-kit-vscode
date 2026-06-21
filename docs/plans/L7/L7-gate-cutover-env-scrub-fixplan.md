---
plan_id: L7-gate-cutover-env-scrub-fixplan
title: "L7-gate-cutover-env-scrub-fixplan: push gate hermetic env から HELIX_DB_CUTOVER/HELIX_DB_DISCOVERY を scrub し cutover leak flake を決定化"
kind: impl
layer: L7
drive: be
status: completed
process_layer: L7
parent_design: HELIX-workflows/helix-process/automation-gate-map.md
tl_review: approve  # tl-advisor (gpt-5.5 high) 諮問 2026-06-22 = 条件付き推奨 A (worker=Opus ≠ reviewer=tl-advisor)。明示2キー scrub・push_gate+conftest 両方・HELIX_DB_* ワイルドカード回避を指示どおり実装。
created: 2026-06-22
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "cutover leak flake: test-isolation scrub(A) vs cross-db FK 実バグ(B) の判定 + scrub 範囲/副作用"
forward_return: "F1-1 着地中に露出した push gate 非決定性 (G-tests flake) の Forward 復帰。逸脱=gate の自家 pytest が ambient migration state(HELIX_DB_CUTOVER) を継承し hermetic 契約が破れた。test-isolation 層 (push_gate._hermetic_test_env + conftest._scrub_gate_context_env) を最小修正し、検証ゲート (G7 実装凍結証跡) を決定的に閉じる。"
pairs_test_design: []
generates:
  - artifact_path: cli/lib/push_gate.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/conftest.py
    artifact_type: python_module
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/plans/L7/L7-f1-code-registration-hookplan.md
  - HELIX-workflows/helix-process/automation-gate-map.md
---

# push gate cutover-env scrub flake-fix Plan

## Purpose

F1-1 (commit 6ed8675) の gate-push が **G-tests のみ間欠 fail** (`1 failed, 2737 passed`) し着地できなかった。他 7 gate は全 PASS、私の手動 `pytest -n auto` は 4/4 緑。**gate でだけ落ちる非決定性**を root-cause し、push gate を決定化する。

## Root Cause（100% 決定的に実証）

- 失敗テスト = `test_harness_monitor_integration.py::TestHarnessMonitorIntegration::test_i_pull_001_get_active_status_filters_session_and_collects_events:198` (`assert status["peak_parallel_today"] >= 2` → `assert 0 >= 2`)。
- env 順列で 100% 再現: **plain=PASS / `HELIX_DB_CUTOVER=1`=FAIL / `HELIX_DB_DISCOVERY=1`=PASS**。
- leak 経路: `db_cli.py:154` が `HELIX_DB_CUTOVER` 既定 `"1"`。`push_gate._hermetic_test_env()` と `conftest._scrub_gate_context_env()` は `HELIX_AUTOMATION_*` / `HELIX_ASKUSERQUESTION_NOW` のみ scrub し、`HELIX_DB_CUTOVER` を素通し → gate 経由で pytest に到達。
- 機構: cutover 下で `compatibility_adapter` の split-DB routing が有効化 (`agent_`→orchestration.db / `automation_`→backend.db)。integration test は seed を explicit `helix_db._write_connection` で legacy DB に入れ、SUT は routed DB を読む。seed と SUT の DB が分裂し、`agent_slots.automation_run_id → automation_runs.id` 等の **cross-DB FK が物理的に不成立** (SQLite FK は同一ファイル内のみ) → new-db write が warning-only で落ち、peak=0。

## 判断（tl-advisor 諮問 2026-06-22）

- **A 採用 (条件付き推奨, decision=passed)**: `HELIX_DB_CUTOVER` の ambient leak による test-isolation 破れとして最小修正し、F1-1 着地を進める。gate の自家 pytest は ambient migration/cutover state に依存させない。
- **B (cross-DB FK) は実 P1 欠陥**だが F1-1 のブロッカーにせず、別 Issue/PLAN で対応 (本 PLAN 末尾 Deferred 参照)。

## 成果物（最小修正、明示 2 キー）

1. `cli/lib/push_gate.py::_hermetic_test_env()`: scrub 集合に `HELIX_DB_CUTOVER` / `HELIX_DB_DISCOVERY` を追加 (gate subprocess = pytest/bats 入口の防御)。`HELIX_DB_PATH` は温存。
2. `cli/lib/tests/conftest.py::_scrub_gate_context_env()`: 同 2 キーを `monkeypatch.delenv` (直接 pytest / 別 runner 経由 leak の pytest 側防御)。
- `HELIX_DB_*` ワイルドカード scrub は禁止 (`HELIX_DB_PATH` 等 test isolation 必須キーを消すため)。明示 2 キーのみ。

## Acceptance（TL 指定の検証戦略、PM 独立実走）

- `test_i_pull_001` plain=PASS。
- `HELIX_DB_CUTOVER=1 pytest <test>`=**PASS** (修正前 FAIL → 修正効果)。
- `HELIX_DB_DISCOVERY=1 pytest <test>`=PASS。
- `test_compatibility_adapter.py`=PASS (明示 cutover/discovery test は body 内 `monkeypatch.setenv` で autouse scrub 後に再設定され無傷: 14 passed, 2 skipped 実証)。
- `bash -n` 相当 = `py_compile` PASS。
- 全 gate (G-tests full tier green + vg_overview overall_clean 維持)。
- tl_review = approve (worker=Opus ≠ reviewer=tl-advisor)。

## Result

- **修正 LANDED 検証**: 上記 Acceptance を PM 独立実走で全 PASS。`HELIX_DB_CUTOVER=1` 下の target が修正前 FAIL → 修正後 PASS を確認 (scrub 効果の直接実証)。`test_compatibility_adapter.py` 14 passed/2 skipped で明示 cutover test の無傷を確認。
- **forward 収束**: push gate の hermetic 契約を ambient migration state 非依存へ強化し、G-tests を決定化。F1-1 着地の gate を開く。

## Deferred（別 Issue/PLAN = TL 指摘 P1/P2/P3）

- **P1**: split-DB cutover で cross-DB FK (`agent_slots.automation_run_id → automation_runs.id` 等、別 bounded-context DB 間) が物理的に不成立。FK を logical reference + consistency detector へ移す / 同一 DB co-locate のいずれかを TL/DBA 判断。**dual-write 期間は warning-only 許容だが cutover final の整合保証としては不可**。→ 別 PLAN (DB separation/cutover finalization) で起票。
- **P2**: integration test が explicit legacy seed と routed SUT を混在。cutover 明示検証では seed/SUT を同一 routing 経路へ揃える必要。
- **P3**: `db_cli.py` の `HELIX_DB_CUTOVER` default `"1"` が gate/test 環境へ伝播しやすい。runbook/env boundary の明文化。
