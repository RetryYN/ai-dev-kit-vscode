---
doc_id: L7-test-design-functional-registry-detector-unit-test
title: functional-registry 検出器 単体テスト設計
status: frozen
freeze_evidence: "2026-06-05 V-model pair-freeze (L6↔L7): UT-FREG-01〜03 を L6 FN-FREG-01〜03 と 1:1。cli/lib/tests/test_functional_registry_checks.py で fixture 実装、pytest 3/3 PASS、trace_symmetry balance1.0/coverage100%/orphan0。逆方向漏れ・重複id・loader fail-close・deprecated skip・advisory=exit0/read-only を反証。詳細は対の L6 doc freeze_evidence 参照"
owner: QA
process_layer: L7
test_layer: L7
parent_design:
  - docs/v2/L6-functional-design/functional-registry-detector-機能設計.md
pairs_design:
  - docs/v2/L6-functional-design/functional-registry-detector-機能設計.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

# functional-registry 検出器 単体テスト設計（L6↔L7 ペア）

> Action1b の L7 成果物。L6 `functional-registry-detector-機能設計.md` の FN-FREG-* と 1:1。`cli/lib/tests/test_functional_registry_checks.py` が TDD で実装する。小さな fixture YAML/MD（数件）で検証し、本番 548件 YAML には依存しない。

## 1. 目的と範囲

- 範囲: FN-FREG-01〜03 の DbC（劣化検出 4 クラス・SSoT 整合・loader fail-close）を単体で反証。
- 非範囲: 548件本番データの中身検証（= 結合/総合）、doctor 統合動作（= 結合）。

## 2. 単体テスト観点

- 検出器は **warn-only（advisory: exit 0）かつ read-only** を常に保つ（finding があっても build を fail させない・disk を変更しない）。
- 劣化検出の核 = **逆方向漏れ**（disk 実在・registry 未登録）と **重複 id** を必ず反証する。
- loader は schema 違反で **fail-close**（部分黙殺なし）。

## 3. 単体テストケース定義（UT-FREG-* ↔ L6 機能設計）

| UT ID | 対象設計 | 検証内容（DbC 観点） | 実装先 |
|---|---|---|---|
| UT-FREG-01 | FN-FREG-01 | fixture で ①path 不在 ②重複 id ③l*_fr 不正 ④逆方向漏れ を各々 Finding 化（ensures）／ deprecated entry の path 不在は非 finding／ advisory=exit0・registry 不変（read-only/warn-only invariant） | `cli/lib/tests/test_functional_registry_checks.py` |
| UT-FREG-02 | FN-FREG-02 | md/yaml fixture の件数差・name 集合差を Finding 化（ensures）／ 整合時は finding 0／ read-only・advisory（invariant） | `cli/lib/tests/test_functional_registry_checks.py` |
| UT-FREG-03 | FN-FREG-03 | 正常 yaml を `list[FunctionalRegistryEntry]` に正規化（ensures）／ 必須欠落・enum 外 domain で `RegistryLoadError`・部分黙殺なし（fail-close invariant） | `cli/lib/tests/test_functional_registry_checks.py` |

## 4. 合格基準（G7 単体）

- UT-FREG-01〜03 が green。逆方向漏れ・重複 id・loader fail-close を必ず反証。
- trace_symmetry: 本 L6↔L7 pair が coverage100% / orphan0 / balance1.0（既存 frozen pair 退行なし）。
- `python3 -m pytest cli/lib/tests/test_functional_registry_checks.py -q` PASS。
