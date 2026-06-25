---
plan_id: L7-v3-engine-phase7-test-cases-projectorplan
title: "L7-v3-engine-phase7-test-cases-projector: Phase 7.3 — project_test_evidence が実 .py/.bats を test_cases へ投影"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/engine/projection-writer.md"
dependencies:
  requires:
    - L7-v3-engine-phase7-code-test-projectorsplan
  blocks: []
pairs_test_design:
  - cli/lib/v3/tests/test_test_cases_projector.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — project_test_evidence が pytest/bats test を test_cases へ投影 (verify-first)"
  - role: qa
    slot_label: "QA — ut_id 導出 / test↔code edge / 重複なし の境界判定"
generates:
  - artifact_path: cli/lib/v3/projection/projectors.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_test_cases_projector.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/engine/projection-writer.md
---

# L7-v3-engine-phase7-test-cases-projector

## 0. 目的

Phase 7.3 = `project_test_evidence` を実 test 対応にし `test_cases` を populate する（現状 0）。これで FN-DET-04(descent-obligation)/FN-DET-05(fn-ut-pair) 等の test 依存 detector が動く土台を作る。`.py`/`.bats` は Phase 7.2 で既に source 集合に在る。

## 0.5 unit 位置づけ

- **unit_id**: U-ENG-P7-TESTCASES / **依存**: C1+C2+Phase7.2(code/test source)。projectors.py の project_test_evidence を完成。
- **scope**: test_cases（+ test↔artifact の test_artifact_edges）。functional_registry/screens/descent は後続 unit。

## 1. 受入条件（DoD）

1. **project_test_evidence**: pytest `test_*.py`/`*_test.py` の各 test 関数 + bats `*.bats` の各 `@test` → `test_cases`（test_cases の実 column = C1 SSoT に map: ut_id/layer/path 等）。**実 repo rebuild で test_cases 行数 > 0**。
2. **ut_id 導出**: test 関数名 / bats test 名から決定的に（規約は projection-writer / C6。無理に発明しない、導出不能は finding でなく skip 可だが silent narrow しない）。
3. **test↔artifact**: test file ↔ artifact_registry(code) の関係を `test_artifact_edges` に（可能な範囲）。
4. **回帰非破壊**: 既存 54 UT green。**2x bit-identical** 維持。code 本文/test 本文を DB 保存しない（C-5）。

## 2. 工程（test-first）

1. RED: `cli/lib/v3/tests/test_test_cases_projector.py`（fixture の .py/.bats → test_cases 投影 / ut_id 導出 / 2x bit-identical）。
2. GREEN: projectors.py の project_test_evidence 完成。
3. 検証: pytest 全 green + 実 repo rebuild で test_cases 行数(>0)。

## 3. 実装方針

- `.py` test 検出 = path に `test_` or `_test` を含む（pytest 規約）。bats = `*.bats` の `@test '<name>'` を AST/正規表現で抽出。
- C1 `test_cases` の実 column のみ map（registry.TABLE_BY_NAME["test_cases"].columns）。無い列は書かない。
- C2 rebuild 枠組み・既存 projector・sources.py は壊さない（project_test_evidence の中身のみ）。

## 4. allowed_files

- `cli/lib/v3/projection/projectors.py` / `cli/lib/v3/tests/test_test_cases_projector.py`。
- 既存 V2/schema/detectors/cutover/sources.py は触らない。

## 5. escalation / 6. 用語 delta / 7. FR delta

schema に無い column を足さない。新規依存禁止。test 本文を DB 保存しない。なし / なし。
