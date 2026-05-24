---
plan_id: L7-test-code-catalog-migration-fixplan
title: "L7-test-code-catalog-migration-fixplan: test_code_catalog::test_migration_v14_to_v15_idempotent assertion 修正 (本 session pytest で検出 unrelated failure)"
kind: troubleshoot
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: cli/lib/helix_db.py
pairs_test_design:
  - docs/plans/L7/L7-test-code-catalog-migration-fixplan.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — スコープ確認・finalize"
  - role: tl-advisor
    slot_label: "TL — migration assertion 修正方針 adversarial check"
  - role: se
    slot_label: "SE — tests/test_code_catalog.py:351 assertion 修正 + test 拡張"
generates:
  - artifact_path: tests/test_code_catalog.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - tests/test_code_catalog.py
  - cli/lib/helix_db.py
  - docs/plans/L7/L7-helix-recover-implplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント (troubleshoot)
> **正本設計 (parent_design)**: cli/lib/helix_db.py (CURRENT_SCHEMA_VERSION 定義 + migration framework)
> **本 PLAN の対象**: 本 session (2026-05-24 第 6 部) 末で pytest 全回帰で検出した `tests/test_code_catalog.py::test_migration_v14_to_v15_idempotent` failure を修正。
> **位置づけ**: 本 session の主要 implementation (recover/route/workflow-skills/doctor-json/vmodel/docs-integration/status-batch) と無関係な既存 test の brittleness 修正。

### 発見経緯

本 session pytest 全回帰 (bg bgiakwh7d、582秒) の結果:
```
2015 passed / 4 skipped / 1 failed
FAILED tests/test_code_catalog.py::test_migration_v14_to_v15_idempotent
  assert [14, 15, 16, 17, 18, 19, ...] == [14, 15, 16, 17, 18, 19, ...]
  Left contains 16 more items, first extra item: 21
```

実際の `schema_version` table は v14-v36 (23 件)、test の期待値は v14-v20 (7 件) 固定 list。本 session で migration v21-v36 が helix.db に追加された (workflow-skills + docs-integration + status-batch + その他の SE 実装で migration framework が拡張された影響) ため、固定 list assertion が brittleness。

### 修正方針

test_code_catalog.py:351 の assertion `assert versions == [14, 15, 16, 17, 18, 19, 20]` の brittleness を修正。

候補 3 案 (tl-advisor R1 で確定):
- 案 A: assertion を最小 7 件確認に変更 `assert versions[:7] == [14, 15, 16, 17, 18, 19, 20]` (最小 7 件、それ以降は許容)
- 案 B: 動的に `assert versions == list(range(14, helix_db.CURRENT_SCHEMA_VERSION + 1))` (実装と test を同期)
- 案 C: 部分集合 check `assert all(v in versions for v in [14, 15, 16, 17, 18, 19, 20])` (subset)

推奨: 案 B (動的、CURRENT_SCHEMA_VERSION と一致を担保、将来 migration 追加でも自動追従)。

## §1 工程表

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | test_code_catalog.py:351 周辺 Read + 設計意図確認 | PM | ✅ done |
| 2 | 修正方針 (案 A/B/C) 比較 + 案 B 推奨理由整理 | PM | ✅ done (§2.A) |
| 3 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 4 | SE 委譲: tests/test_code_catalog.py 修正 | PM → SE | □ pending |
| 5 | pytest test_code_catalog.py 単体 PASS 確認 | SE | □ pending |
| 6 | pytest 全回帰 (2015+ PASS / 0 failed 復帰確認) | SE | □ pending |
| 7 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A 修正案 (案 B 推奨、動的 CURRENT_SCHEMA_VERSION 同期)

**現状 (test_code_catalog.py:351 付近)**:
```python
version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
columns = {row[1] for row in conn.execute("PRAGMA table_info(code_index)").fetchall()}
row = conn.execute("SELECT id, symbol_line, bucket FROM code_index WHERE id = 'legacy.entry'").fetchone()
versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")]
conn.close()

assert version == helix_db.CURRENT_SCHEMA_VERSION
assert versions == [14, 15, 16, 17, 18, 19, 20]   # ← brittleness、固定 list
assert {"bucket", "symbol_line"} <= columns
assert row == ("legacy.entry", 7, "coverage_eligible")
```

**修正案 B (推奨)**:
```python
# 動的に CURRENT_SCHEMA_VERSION と一致を担保
assert versions == list(range(14, helix_db.CURRENT_SCHEMA_VERSION + 1))
```

理由:
- migration v14-v20 という固定 list は将来 migration 追加 (本 session で v21-v36 追加済) で brittleness
- 動的 assertion で実装と test が同期、将来 migration 追加でも自動追従
- 案 A (versions[:7]) は v14-v20 のみ確認、v21+ の整合性を見ない (subset)
- 案 C (all in) は順序不問、SQL `ORDER BY version` の意図を弱体化

### §2.B test 単体実行確認

修正後の検証:
```bash
python3 -m pytest tests/test_code_catalog.py::test_migration_v14_to_v15_idempotent -v
# 期待: PASSED
```

### §2.C 関連 test の調査

migration assertion を持つ他 test の確認:
```bash
grep -n "versions ==" tests/test_code_catalog.py cli/lib/tests/test_helix_db*.py
```
類似 brittleness pattern があれば併せて修正 (本 PLAN scope に含む or 別 PLAN 候補)。

### §2.D pytest 全回帰確認

修正後の全回帰確認:
```bash
python3 -m pytest cli/lib/tests/ tests/ -q
# 期待: 2015 → 2016 passed / 0 failed (本 PLAN fix で復帰)
```

## §3 成果物

- tests/test_code_catalog.py 修正 (assertion 1-2 行変更、~5 行 diff)

副次:
- (必要なら) 類似 brittleness 持つ他 test の併修正

## §4 受入条件 / DoD

- [ ] python3 -m pytest tests/test_code_catalog.py::test_migration_v14_to_v15_idempotent PASSED
- [ ] python3 -m pytest tests/test_code_catalog.py 全 PASS (regression なし)
- [ ] python3 -m pytest cli/lib/tests/ tests/ -q で **0 failed** (本 PLAN 完遂で 1 failed → 0 failed 復帰)
- [ ] helix_db.CURRENT_SCHEMA_VERSION との整合 (将来 migration 追加で test 自動追従)
- [ ] plan_validator warnings 0

## §5 関連 PLAN / docs

- 関連 file: tests/test_code_catalog.py:351
- 関連 module: cli/lib/helix_db.py (CURRENT_SCHEMA_VERSION + migration framework)
- 発見契機: 本 session pytest 全回帰 bg bgiakwh7d で検出
- 本 session 実装 PLAN (本 PLAN とは独立、scope 外): L7-helix-recover-implplan v3 / L7-helix-route-implplan v3 / L7-workflow-skills-pkgplan v3 / L7-docs-integration-mappingplan v2 / L7-helix-workflows-status-acceptedplan v2 / L7-helix-doctor-json-implplan v2 / L7-helix-vmodel-show-injection-implplan

## §6 後続 PLAN 候補

- 他 brittleness pattern (固定 list assertion) を持つ test の整理 (helix doctor / migration / catalog 系)
- migration framework の version 追加時の test 自動更新 hook (pre-commit or CI)
