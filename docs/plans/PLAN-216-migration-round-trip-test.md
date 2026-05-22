---
plan_id: PLAN-216
title: "PLAN-216: helix.db migration round-trip test framework v2 (up/down/verify 強化)"
layer: L4
kind: impl
status: draft
size: M
drive: db
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: dba
    slot_label: "DBA — fixture data 設計 + anonymization 方針確定 + round-trip cycle 設計"
  - role: se
    slot_label: "SE — cli/lib/migration_round_trip.py 新規実装 + round_trip runner"
  - role: qa
    slot_label: "QA — up → verify → down → up 4-phase cycle test 設計・実装 (v32〜v36)"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-132 依存整合・helix doctor 統合設計レビュー・G4 review"
generates:
  - artifact_path: cli/lib/migration_round_trip.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_migration_round_trip.py
    artifact_type: test
  - artifact_path: cli/lib/tests/fixtures/migration_round_trip/
    artifact_type: other
  - artifact_path: docs/plans/PLAN-216-migration-round-trip-test.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-132
  requires:
    - PLAN-132
  blocks: []
related_plans:
  - PLAN-132-helix-db-migration-test-framework
  - PLAN-086-helix-db-rollback-cli
related_adr: []
related_docs:
  - cli/lib/migration_test_framework.py
  - cli/lib/migrations/
  - cli/lib/helix_db.py
---

# PLAN-216: helix.db migration round-trip test framework v2

> **kind**: impl | **layer**: L4 | **drive**: db | **parent**: PLAN-132

---

## §0. 本 PLAN の位置付け

PLAN-132 が確立した `MigrationBase` (up / down / verify 3-method 規約) の発展 PLAN。
PLAN-132 は空 DB 上の cycle test を整備したが、**fixture data を使った populated DB での
round-trip** は未実装。本 PLAN はその空白を埋め、helix doctor に統合する。

---

## §1. 目的

1. `cli/lib/migration_round_trip.py` 新規実装 — fixture ベースの `up → verify → down → up` 4-phase cycle runner
2. `cli/lib/tests/fixtures/migration_round_trip/` に anonymized fixture YAML (v32〜v36) を配置
3. pytest で v32〜v36 全件の `run_round_trip()` が PASS
4. `helix doctor check_migration_round_trip` を追加し、G4 ゲートで自動確認

---

## §2. 設計方針

### 2.1 PLAN-132 との差分

| 観点 | PLAN-132 | 本 PLAN |
|---|---|---|
| DB 初期状態 | 空 DB | fixture data あり (populated) |
| 検証対象 | schema 構造 | data 整合性 + schema 構造 |
| helix doctor check | check_migration_coverage | check_migration_round_trip |

### 2.2 fixture data 方針

- PII 不含。plan_id は `PLAN-TEST-NNN`、task summary は lorem ipsum
- version 別 YAML: `cli/lib/tests/fixtures/migration_round_trip/v{NN}_fixture.yaml`
- `RoundTripRunner` は tmpdir に isolation した DB を生成 (helix-db.lock 競合防止)

### 2.3 `RoundTripRunner` API

```python
class RoundTripRunner:
    def __init__(self, migration_cls, fixture_path=None, db_path=None): ...
    def load_fixture(self) -> None: ...
    def run_round_trip(self) -> RoundTripResult: ...
    def assert_clean(self) -> None: ...
```

`RoundTripResult` は 4 phase (up_1 / verify / down / up_2) それぞれの row_counts とエラーを保持。
up_1 と up_2 で row_count が一致することを assert する。

### 2.4 helix doctor 統合

`check_migration_round_trip`: PASS (全 cycle OK) / WARN (fixture なし、空 DB のみ検証) / FAIL (cycle 失敗)

---

## §3. DoD

- [ ] `cli/lib/migration_round_trip.py` (`RoundTripRunner` + `RoundTripResult`) 実装
- [ ] fixture YAML: `cli/lib/tests/fixtures/migration_round_trip/v32〜v36_fixture.yaml`
- [ ] `test_migration_round_trip.py` で v32〜v36 全件 `run_round_trip()` PASS
- [ ] `helix doctor check_migration_round_trip` が PASS / WARN / FAIL を返す
- [ ] `python3 -m py_compile cli/lib/migration_round_trip.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_migration_round_trip.py -v` 全件 PASS
- [ ] pytest 全体 sweep で regression なし

---

## §4. 実装計画

### Sprint .1 — skeleton + fixture 設計 (DBA + SE)

- `MigrationBase` import 構造確認 (PLAN-132 生成物 Read)
- `migration_round_trip.py` skeleton (`RoundTripResult` dataclass + `RoundTripRunner` stub)
- fixture YAML schema 策定 + `tests/fixtures/migration_round_trip/` ディレクトリ作成
- 受入: `py_compile` PASS + fixture schema コメント明記

### Sprint .2 — fixture 実装 + `run_round_trip` 完成 (DBA + SE)

- v32〜v35 の fixture YAML 実装 (anonymized rows)
- `load_fixture()` + `run_round_trip()` 実装 (4-phase cycle + row_count 記録)
- T1〜T4 (v32〜v35 round-trip) 実装
- 受入: T1〜T4 PASS / row_count が up_1 = up_2 であることを assert

### Sprint .3 — helix doctor + v36 + 全体検証 (SE + QA)

- PLAN-116 v36 fixture YAML + T5 実装
- `helix doctor check_migration_round_trip` 追加
- pytest 全体 sweep で regression 確認
- 受入: T1〜T5 全 PASS / helix doctor 出力確認 / regression なし

---

## §5. リスクと緩和策

| リスク | 緩和策 |
|---|---|
| PLAN-132 未完成で blocking | Sprint .1 entry 前に PLAN-132 DoD 確認必須 |
| fixture が schema 変更で stale | version 別 YAML 分離。migration 追加時に fixture 追加を DoD に含める |
| v34 down() が partial | row_count exact match でなく「≤ up 前」を許容する assert モードを設ける |
| v36 が Sprint .3 時点で未完 | T5 を `pytest.mark.skip` で条件付き実行 (PLAN-116 完了後に有効化) |

---

## §6. V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN) | docs/plans/PLAN-216-migration-round-trip-test.md |
| ② 実装コード | cli/lib/migration_round_trip.py |
| ③ テスト設計 (予定) | docs/v2/L4-test-design/PLAN-216-round-trip-test-design.md |
| ④ テストコード | cli/lib/tests/test_migration_round_trip.py |

双方向 reference: 実装コード docstring に「設計: PLAN-216」、テストコード docstring に
「DoD 検証: PLAN-216 §3」を追記する。

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
