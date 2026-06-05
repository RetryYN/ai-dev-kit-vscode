---
doc_id: L7-test-design-coding-rule-detector-unit-test
title: coding-rule 検出器 単体テスト設計
status: frozen
freeze_evidence: "2026-06-06 V-model pair-freeze (L6↔L7): UT-CRREG-01〜04 を FN-CRREG-01〜04 と 1:1 に固定。pytest 4 case、baseline deterministic、doctor warn-only 連携、trace_symmetry balance1.0/coverage100%/orphan0 を確認する。"
owner: QA
process_layer: L7
test_layer: L7
parent_design:
  - docs/v2/L6-functional-design/coding-rule-detector-機能設計.md
pairs_design:
  - docs/v2/L6-functional-design/coding-rule-detector-機能設計.md
artifact_type: design_doc
---

# coding-rule 検出器 単体テスト設計（L6↔L7 ペア）

> Action2 の L7 成果物。`coding_rule_checks.py` の loader / detector / baseline CLI を fixture ベースで固定し、doctor 配線より前に公開契約を TDD で凍結する。

## 1. 目的

- FN-CRREG-01〜04 を最小 fixture で反証する。
- warn-only / read-only / deterministic baseline の invariant をテストで固定する。
- `functional-registry.yaml` への自資産登録漏れを detector の責務として固定する。

## 2. 単体テスト観点

- schema 違反は `RegistryLoadError` で fail-close する。
- `manual / partial / not-implemented` は gap finding として surface する。
- `status=enforced` かつ `paths=[]` は detector finding とする。
- baseline JSON は同一入力で不変、CLI は生成 path を返す。

## 3. 単体テストケース定義（UT-CRREG-* ↔ L6）

| UT ID | 対象設計 | 検証内容 | 実装先 |
|---|---|---|---|
| UT-CRREG-01 | FN-CRREG-01 | 正常 registry を正規化し、必須欠落 / enum 外で `RegistryLoadError` を返す | `cli/lib/tests/test_coding_rule_checks.py` |
| UT-CRREG-02 | FN-CRREG-02 | enforcement gap、missing path、status/path mismatch、self asset 未登録を advisory finding 化し、入力 YAML は不変 | `cli/lib/tests/test_coding_rule_checks.py` |
| UT-CRREG-03 | FN-CRREG-03 | CLAUDE.md 3 節の total/per-section drift を finding 化し、整合時は finding 0 | `cli/lib/tests/test_coding_rule_checks.py` |
| UT-CRREG-04 | FN-CRREG-04 | baseline payload が deterministic、fingerprint 付きで、`main --emit-baseline` が JSON を書いて path を返す | `cli/lib/tests/test_coding_rule_checks.py` |

## 4. 合格基準

- `python3 -m pytest cli/lib/tests/test_coding_rule_checks.py -q` PASS。
- UT-CRREG-01〜04 が 1:1 で green。
- trace_symmetry で L6/L7 pair の coverage 100%、orphan 0、balance 1.0。
