---
plan_id: L7-v3-engine-phase8-core-detectorsplan
title: "L7-v3-engine-phase8-core-detectors: Phase 8.1 — detector runner (ok=AND) + FN-DET-01/02/03 (pure-function 3層)"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/engine/detector-wiring.md"
dependencies:
  requires:
    - L7-v3-engine-phase7-core-projectorsplan
  blocks: []
pairs_test_design:
  - cli/lib/v3/tests/test_core_detectors.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — detector runner(ok=AND, fail-close) + FN-DET-01/02/03 pure-function 3層 (verify-first)"
  - role: qa
    slot_label: "QA — analyze 純関数性 / absence=ok=false / もれ検出境界 / source_kind の判定"
generates:
  - artifact_path: cli/lib/v3/detectors/__init__.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/detectors/runner.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/detectors/core.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_core_detectors.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/engine/detector-wiring.md
  - docs/v3/L0-L14/L6-functional-design.md
---

# L7-v3-engine-phase8-core-detectors

## 0. 目的

Phase 8.1 = V3 keystone **C3 detector の最小実体**を作る。detector runner（`run_doctor`、ok=AND、fail-close）+ 最初の 3 detector（[L6 FN-DET-01/02/03](../../v3/L0-L14/L6-functional-design.md)）を pure-function 3 層（[C3 契約](../../v3/engine/detector-wiring.md)）で実装。Phase 7 で populate 済の plan_registry/artifact_registry/trace_edges を query する（db_projection source）。

## 0.5 unit 位置づけ

- **unit_id**: U-ENG-P8-CORE / **依存**: C1(schema)+C2/Phase7(populated tables)。
- **scope**: runner + FN-DET-01(plan-artifact-existence)/FN-DET-02(plan-completion-drift)/FN-DET-03(trace-symmetry)。残り ~57 detector + lint-wiring + baseline は後続 unit。

## 1. 受入条件（DoD）

1. **runner**: `run_doctor(db, detectors) -> DoctorResult{ok, findings}`。`ok = all(d.ok for d in hard)`（短絡せず全 detector 実行、findings 全件収集）。I/O 失敗 = ok=false（fail-close）。soft/advisory は ok を落とさず surface。
2. **Detector 様式（3 層、全 detector 遵守）**: `analyze_<x>(input)->Result` 純関数（I/O なし）/ `load_<x>_input(db)->Input` で query 隔離 / `<x>_messages(result)->list[Finding]`。各 detector に `source_kind: db_projection|file_snapshot|hybrid` + `severity`。
3. **FN-DET-01 plan-artifact-existence**: plan_registry の各 PLAN が generates する artifact が artifact_registry に未実在 → finding。
4. **FN-DET-02 plan-completion-drift**: artifact 実在なのに plan status=draft 放置（逆 drift）→ finding（file を stat しない、artifact_registry の実在で判定）。
5. **FN-DET-03 trace-symmetry**: trace_edges の片方向 edge（双方向非対称 orphan）→ finding。
6. **absence=ok=false**: source（DB row）不在・空でも `ok=false`（scope-0 silent OK 禁止）。
7. **Finding 機械可読**: `{id, severity, subject, missing}`。
8. **回帰非破壊**: 既存 43 UT green。

## 2. 工程（test-first）

1. **RED**: `cli/lib/v3/tests/test_core_detectors.py` に UT（各 detector の analyze を pure に呼ぶ fixture / もれあり→finding / もれなし→ok / absence→ok=false / runner ok=AND）を先に書き fail。
2. **GREEN**: `detectors/{runner,core,__init__}.py` 実装。
3. 検証: `pytest cli/lib/v3/tests/ -q` 全 green + 実 repo（rebuild 済 DB）に run_doctor を流して findings が機械可読で返ることを確認。

## 3. 実装方針

- **stdlib のみ**（sqlite3）。`from v3.schema import registry`。
- analyze は**必ず純関数**（input struct を受け取り result を返す。fs/DB 触らない）。loader が DB query を隔離。
- detector は dataclass か Protocol で `{analyze, load, messages, source_kind, severity}` を表現。
- runner は hard detector の AND で ok、short-circuit しない。
- C1/C2/projector/cutover は触らない（detector は別ディレクトリ cli/lib/v3/detectors/）。

## 4. allowed_files

- `cli/lib/v3/detectors/*.py`（新規）/ `cli/lib/v3/tests/test_core_detectors.py`（新規）
- 既存 V2 / schema / projection / cutover は import のみ。

## 5. escalation

- schema に無い column を query しない（C1 SSoT）。analyze に I/O を混ぜない（pure 厳守）。設計矛盾は止めて PM へ。

## 6. 用語 delta / 7. FR delta

なし（FN-DET-01/02/03 + runner の実装。新規 FR なし）。
