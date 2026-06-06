---
doc_id: L7-test-design-registry-detector-unit-test
title: 登録・検出 共通基盤 単体テスト設計
status: frozen
freeze_evidence: "2026-06-05 V-model pair-freeze (L6↔L7 base): UT-RDB-01〜07 を L6 FN-RDB-01〜07 と 1:1。cli/lib/tests/test_registry_checks.py で実装、pytest 7/7 PASS、trace_symmetry balance1.0/coverage100%/orphan0。PM 独立 invariant probe 10/10 PASS。詳細は対の L6 doc freeze_evidence 参照"
owner: QA
process_layer: L7
test_layer: L7
parent_design:
  - docs/v2/L6-functional-design/registry-detector-機能設計.md
pairs_design:
  - docs/v2/L6-functional-design/registry-detector-機能設計.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

# 登録・検出 共通基盤 単体テスト設計（L6↔L7 ペア）

> Action1 の L7 成果物。L6 `registry-detector-機能設計.md` の FN-RDB-* と 1:1。`cli/lib/tests/test_registry_checks.py` が本設計を TDD で実装する（テスト先行）。

## 1. 目的と範囲

- 範囲: 共通基盤 5 型の公開契約（FN-RDB-01〜07）の DbC（requires / ensures / invariant）を単体で反証する。
- 非範囲: 個別 detector の判定、YAML data の中身検証、doctor 統合（= Action1b 以降の結合/総合テスト）。

## 2. 単体テスト観点

- 正常系（ensures）と異常系（invariant の fail-close）を必ず対で置く。
- GatePolicy は **mode 別に exit code の境界**（advisory=常に0 / ratchet=新規違反のみ非0 / fail_close=P0/P1 で非0）を検証する。
- promote は **段階 skip 拒否**と **evidence 不足拒否**を反証する。

## 3. 単体テストケース定義（UT-RDB-* ↔ L6 機能設計）

| UT ID | 対象設計 | 検証内容（DbC 観点） | 実装先 |
|---|---|---|---|
| UT-RDB-01 | FN-RDB-01 | yaml/md を正規化 list[RegistryEntry] に読む（ensures）／ 解析不能・必須欠落で `RegistryLoadError`・部分黙殺しない（fail-close invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDB-02 | FN-RDB-02 | 充足 mapping を正規化（paths/patterns/traces を list 化, ensures）／ 必須 field 欠落で `ValidationError`・silent default なし（invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDB-03 | FN-RDB-03 | 正常 severity で frozen Finding 生成（ensures）／ enum 外 severity・空 kind で生成時 error（invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDB-04 | FN-RDB-04 | findings+mode から exit_policy 付き report を生成（ensures）／ 不正 mode で error（invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDB-05 | FN-RDB-05 | advisory は findings 有でも exit0／ ratchet は baseline 比 新規違反のみ非0／ fail_close は P0/P1 で非0（ensures + advisory=exit0 invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDB-06 | FN-RDB-06 | evidence 5 条件充足で advisory→ratchet→fail_close 昇格（ensures）／ 段階 skip 拒否・evidence 不足で昇格拒否（fail-close invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDB-07 | FN-RDB-07 | text/json で人間・機械可読出力（ensures）／ findings が severity,entry_id で決定的順序（invariant） | `cli/lib/tests/test_registry_checks.py` |
| UT-RDC-01 | FN-RDC-01 | clean registry で 0 findings／unknown_coverage_layer・enum外検出／L4 空 design_ids=`design_id_missing`／L6 空=`l6_design_pending`(区別)／excluded_reason 無効検出／design_id 未解決検出／coverage_layer↔prefix 不整合=`wrong_layer`／L6+FN-* は clean／非active skip（10 ケース、ensures+invariant 反証） | `cli/lib/tests/test_registry_design_coverage_checks.py` |

## 4. 合格基準（G7 単体）

- UT-RDB-01〜07 が green（7 ケース以上。1 FN に正常+異常で複数 assert 可）。
- trace_symmetry: L6↔L7 で本 pair が coverage100% / orphan0 / balance1.0（既存 14↔14 frozen pair を退行させない）。
- `python3 -m pytest cli/lib/tests/test_registry_checks.py -q` PASS、`helix doctor` の既存 `24-0-105` を退行させない。
