---
plan_id: L7-v3-engine-phase7-code-test-projectorsplan
title: "L7-v3-engine-phase7-code-test-projectorsplan: Phase 7.2 — code + test projectors (artifact_registry/test_cases/test_results)"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/engine/projection-writer.md"
dependencies:
  requires:
    - L7-v3-engine-phase7-core-projectorsplan
  blocks: []
pairs_test_design:
  - cli/lib/v3/tests/test_code_test_projectors.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — project_code/project_test_evidence が実 cli/** code + pytest/bats を投影 (verify-first)"
  - role: qa
    slot_label: "QA — code/test 投影行数 / test↔code trace / unresolved-join 減少の境界判定"
generates:
  - artifact_path: cli/lib/v3/projection/projectors.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_code_test_projectors.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/engine/projection-writer.md
  - docs/v3/engine/schema-registry.md
---

# L7-v3-engine-phase7-code-test-projectorsplan

## 0. 目的

Phase 7.2 = code + test projector を完成し `artifact_registry`(code) / `test_cases` / `test_results` / `test_artifact_edges` を実 source から投影する。Phase 7.1 で残った **unresolved-join（trace_edges が未投影の code/test artifact を指す、~1678 件）を実質削減**する。

## 0.5 unit 位置づけ

- **unit_id**: U-ENG-P7-CODETEST / **parent**: Phase 7.1（projectors.py を継続完成） / **依存**: C1+C2+Phase7.1。
- **scope**: `cli/**/*.py` `cli/helix*` → artifact_registry(code) / pytest `test_*.py` + bats `*.bats` → test_cases/test_results/test_artifact_edges。gate/FR/screen/descent/review projector は Phase 7.3。

## 1. 受入条件（DoD）

1. **project_code**: `cli/**/*.py` + `cli/helix*`（実ファイル列挙は C2 source-completeness の git→fs fallback 経由）→ `artifact_registry`（artifact_type=python_module/script、path、content_hash、status）。行数 > 0。
2. **project_test_evidence**: pytest `test_*.py` + bats `*.bats` → `test_cases`（ut_id/layer/path）。実行結果が無い段階では `test_results` は空 or pending（実行証跡は別途）。test↔artifact は `test_artifact_edges`。
3. **unresolved-join 減少**: 実 repo（`docs/plans` + `cli`）rebuild で unresolved-join が Phase 7.1 比で**有意に減る**（code/test artifact が解決される分）。
4. **回帰非破壊**: 既存 40 UT 全 green。**2x bit-identical** 維持。
5. **secret-safe**: code 投影で raw secret を DB に入れない（C-5、content_hash と path のみ、本文は保存しない）。

## 2. 工程（test-first）

1. **RED**: `cli/lib/v3/tests/test_code_test_projectors.py` に UT（fixture + 実 cli 投影行数 / test_cases 投影 / unresolved-join 減少 / 2x bit-identical）を先に書き fail。
2. **GREEN**: `projectors.py` に project_code / project_test_evidence を実装。
3. 検証: `pytest cli/lib/v3/tests/ -q` 全 green + 実 repo rebuild で artifact_registry(code)/test_cases 行数 + unresolved-join 減少を確認。

## 3. 実装方針

- C1 schema の実 column へ map（`artifact_registry` / `test_cases` / `test_results` / `test_artifact_edges` の存在列のみ）。
- code 本文は **保存しない**（path + content_hash + artifact_type のみ。secret 混入回避 = C-5）。
- ut_id は test 関数名 / bats test 名から導出（規約は projection-writer / C6 に従う。無理に発明しない）。
- C2 の rebuild 枠組み・既存 projector は壊さない。

## 4. allowed_files

- `cli/lib/v3/projection/projectors.py`（継続完成）/ `cli/lib/v3/tests/test_code_test_projectors.py`（新規）
- **既存 V2 / schema / cutover / sources.py は触らない**。

## 5. escalation

- schema に無い column を足さない。新規依存禁止。code 本文を DB に保存しない（C-5）。設計矛盾は止めて PM へ。

## 6. 用語 delta / 7. FR delta

なし。
