---
doc_id: L7-test-design-ddd-registry-detector-unit-test
title: DDD registry 検出器 単体テスト設計
status: frozen
freeze_evidence: "2026-06-06 V-model pair-freeze (L6↔L7): UT-DDD-01〜05 を FN-DDD-01〜05 と 1:1 に固定。pytest 5 case、baseline deterministic、doctor warn-only 連携、trace_symmetry balance1.0/coverage100%/orphan0 を確認する。"
owner: QA
process_layer: L7
test_layer: L7
parent_design:
  - docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
pairs_design:
  - docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
artifact_type: design_doc
---

# DDD registry 検出器 単体テスト設計（L6↔L7 ペア）

> Action3 の L7 成果物。`ddd_registry_checks.py` の loader / 3 detector / baseline CLI を fixture ベースで固定し、doctor 配線より前に公開契約を TDD で凍結する。

## 1. 目的

- FN-DDD-01〜05 を最小 fixture で反証する。
- warn-only / read-only / deterministic baseline の invariant をテストで固定する。
- `check_ubiquitous_language` を scope 外に留めたまま DDD 構造 coverage の 3 check だけを実装する。

## 2. 単体テスト観点

- schema 違反は `RegistryLoadError` で fail-close する。
- glossary row drift / duplicate / 欄欠落 / invalid enum は advisory finding として surface する。
- BC 欄欠落、§14.2 越境例不足、mode 漏れは advisory finding とする。
- baseline JSON は同一入力で不変、CLI は生成 path を返す。

## 3. 単体テストケース定義（UT-DDD-* ↔ L6）

| UT ID | 対象設計 | 検証内容 | 実装先 |
|---|---|---|---|
| UT-DDD-01 | FN-DDD-01 | 正常 registry を正規化し、section 欠落 / 必須 key 欠落 / **BC `kind` enum 外**で `RegistryLoadError` を返す（`implementation_status` enum 値違反は loader で落とさず UT-DDD-02 で advisory finding 化） | `cli/lib/tests/test_ddd_registry_checks.py` |
| UT-DDD-02 | FN-DDD-02 | glossary row drift、term duplicate、列欠落、invalid enum、implementation gap を advisory finding 化し、入力 YAML は不変 | `cli/lib/tests/test_ddd_registry_checks.py` |
| UT-DDD-03 | FN-DDD-03 | `unique_terms` / `anti_corruption_via` 欠落と §14.2 越境例不足を finding 化する | `cli/lib/tests/test_ddd_registry_checks.py` |
| UT-DDD-04 | FN-DDD-04 | Forward 1 + derived 9 の mode coverage 漏れ / 余剰 mode を finding 化する | `cli/lib/tests/test_ddd_registry_checks.py` |
| UT-DDD-05 | FN-DDD-05 | baseline payload が deterministic、fingerprint 付きで、`main --emit-baseline` が JSON を書いて path を返す | `cli/lib/tests/test_ddd_registry_checks.py` |

## 4. 合格基準

- `python3 -m pytest cli/lib/tests/test_ddd_registry_checks.py -q` PASS。
- UT-DDD-01〜05 が 1:1 で green。
- trace_symmetry で L6/L7 pair の coverage 100%、orphan 0、balance 1.0。
