---
plan_id: PLAN-132
title: "PLAN-132: helix-db migration test framework — up/down/verify 3-method 規約 + pytest 自動化"
layer: L4
kind: impl
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-116-helix-db-v36-schema.md   # from dependencies.parent
size: M
drive: db
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: dba
    slot_label: "DBA — migration test framework 設計 + 3-method 規約定義 + 既存 v32-v36 migration retrofit"
  - role: se
    slot_label: "SE — cli/lib/migration_test_framework.py 新規実装 + helix db CLI 拡張 (--dry-run/--verify/--rollback)"
  - role: qa
    slot_label: "QA — up→verify→down→up cycle test 設計・実装 (全 5 migration)"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-116/PLAN-086 との依存整合・G4 review"
  - role: tl-advisor
    slot_label: "TL adversarial check — framework API 設計・idempotency 保証・ADR-047 凍結判定"
generates:
  - artifact_path: cli/lib/migration_test_framework.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_migration_framework.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-047-migration-test-framework.md
    artifact_type: adr_snapshot
  - artifact_path: docs/plans/PLAN-132-helix-db-migration-test-framework.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-116
  requires:
    - PLAN-116
  blocks: []
related_plans:
  - PLAN-086-helix-db-rollback-cli
  - PLAN-116-helix-db-v36-schema
related_adr:
  - ADR-047-migration-test-framework
related_docs:
  - cli/lib/helix_db.py
  - cli/lib/migrations/
---

# PLAN-132: helix-db migration test framework

> **kind**: impl (migration test framework 新規実装)
> **layer**: L4 (実装フェーズ)
> **drive**: db (helix.db migration 体系化)
> **L2 凍結**: ADR-047 (3-method 規約 + framework API 設計、L2 大局判断)

---

## §0. 本 PLAN の位置付け

本 PLAN は helix.db の migration test を体系化する実装 PLAN。
PLAN-116 (helix.db v36 schema) が parent PLAN であり、v35 → v36 migration が実装される
タイミングで、過去 v32〜v35 も含む全 migration script の test coverage を確立する。

PLAN-086 (helix db rollback CLI) が rollback の実行機構を提供しており、本 PLAN はその
test 検証面を補完する。

---

## §1. 目的

1. 各 migration script に `up()` / `down()` / `verify()` の 3-method 規約を必須化し、
   machine-testable な状態にする
2. `cli/lib/migration_test_framework.py` を新規実装し、全 migration の
   `up → verify → down → up` cycle を pytest で自動化する
3. `helix db migrate --dry-run` / `--verify` / `--rollback` の CLI を拡張し、
   手動検証と CI での自動検証を統一する
4. 新規 migration (v36 以降) は本 framework に準拠することを HELIX 標準とする

---

## §2. 背景

### 2.1 現状の問題

HELIX では v32 → v33 → v34 → v35 と migration が積み重なっているが、
各 migration の test は散在している:

| migration | test 状況 | 問題 |
|---|---|---|
| v32 (plan_registry 前身) | test_helix_db_v19 に一部含まれる | version 番号ズレ、専用 test なし |
| v33 (schema_version table 化) | PLAN-089 後追いで test_helix_gate が兼用 | migration 専用 test なし |
| v34 (todo_entries / v34_todo_entries chain) | Wave 3 で test 4/4 追加 | up/down cycle なし |
| v35 (plan_registry / task_queue 拡張) | test_helix_db_v19 系で断片的 | rollback test なし |
| v36 (PLAN-116 予定) | 未実装 | framework 不在のまま実装予定 |

2026-05-23 の pytest sweep で **1846 test PASS** だが、migration の `down()` / rollback
cycle が test されていないため、rollback が必要な本番事故時に動作未確認のコードを使う
リスクがある (PLAN-086 rollback CLI との連携も未検証)。

### 2.2 設計根拠

- SQLite の migration best practice: Alembic (Python 界) / Flyway (JVM 界) ともに
  up/down の対称性を migration の基本単位とする。HELIX は SQLite + Python であり、
  Alembic の `upgrade()` / `downgrade()` pattern を参考にする。
- `verify()` の追加: HELIX 固有の要件として、migration 後の schema 整合性を
  helix.db 内で自己検証する。既存 `helix doctor` の design_doc / ADR 系 check と
  同じ pattern (PASS / FAIL / WARN) を採用する。
- `--dry-run`: SQLite の `BEGIN; ... ROLLBACK;` pattern で migration SQL を
  実行せずに構文検証する。

---

## §3. 設計方針 (L2 凍結 → ADR-047)

### 3.1 migration 3-method 規約

```python
# cli/lib/migrations/vNN_example.py (規約)
from cli.lib.migration_test_framework import MigrationBase

class Migration(MigrationBase):
    version = NN
    description = "..."

    def up(self, conn) -> None:
        """schema を vNN に上げる。idempotent 必須 (IF NOT EXISTS 等)。"""
        ...

    def down(self, conn) -> None:
        """schema を v(NN-1) に戻す。up() の完全な逆操作。"""
        ...

    def verify(self, conn) -> list[str]:
        """up() 後の整合性を確認。エラー文字列 list を返す (空 = PASS)。"""
        ...
```

**設計選択の根拠 (ADR-047 で凍結)**:
- クラスベース (`MigrationBase` 継承) — Alembic env.py パターン準拠、型安全
- `verify()` が list[str] を返す — エラーメッセージを機械可読にし、helix doctor に接続可能
- `idempotent` 必須 — `helix db migrate` を複数回実行しても副作用なし

### 3.2 test framework API

```python
# cli/lib/migration_test_framework.py
class MigrationTestRunner:
    def __init__(self, migration_cls: type[MigrationBase], db_path: str | None = None)
    def run_up(self) -> None
    def run_down(self) -> None
    def run_verify(self) -> list[str]
    def run_cycle(self) -> None  # up → verify → down → up → verify の complete cycle
    def assert_clean(self) -> None  # 0 エラーを assert
```

### 3.3 CLI 拡張

```
helix db migrate [--version NN] [--dry-run] [--verify] [--rollback]
```

| flag | 動作 |
|---|---|
| (none) | 最新まで up (既存動作) |
| `--dry-run` | BEGIN; up SQL; ROLLBACK; で構文確認のみ |
| `--verify` | up() 後に verify() を実行、エラーあれば exit 1 |
| `--rollback` | 現バージョンの down() を実行 → PLAN-086 rollback と連携 |

---

## §4. DoD (Definition of Done)

- [ ] `cli/lib/migration_test_framework.py` に `MigrationBase` + `MigrationTestRunner` を実装
- [ ] 既存 migration v32〜v35 に `up()` / `down()` / `verify()` 3-method を retrofit
- [ ] PLAN-116 の v36 migration を最初から 3-method 規約で実装
- [ ] `cli/lib/tests/test_migration_framework.py` で v32〜v36 全件の `run_cycle()` が PASS
- [ ] `helix db migrate --dry-run` / `--verify` / `--rollback` が動作する
- [ ] ADR-047 を L2 大局判断 snapshot として起票 (本 PLAN 起票時点では placeholder)
- [ ] `python3 -m py_compile cli/lib/migration_test_framework.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_migration_framework.py -v` 全件 PASS
- [ ] `python3 -m pytest cli/lib/tests/` 全体 sweep で regression なし

---

## §5. 実装計画

### Sprint .1 — framework 設計 + MigrationBase skeleton

**担当**: DBA + SE

**作業**:
1. ADR-047 起票 (L2 大局判断凍結): 3-method 規約 + `MigrationTestRunner` API
2. `cli/lib/migration_test_framework.py` 実装:
   - `MigrationBase` abstract class (`up` / `down` / `verify` を abstractmethod)
   - `MigrationTestRunner` class (3.2 の API 通り)
   - `create_test_db()` helper — pytest fixture 用の in-memory SQLite DB 生成
   - `apply_migrations_up_to(conn, version)` — version まで順次 up() を適用
3. `cli/lib/tests/test_migration_framework.py` skeleton:
   - fixture: `tmp_db` (tmpdir + fresh SQLite)
   - T1: `MigrationBase` を継承した mock migration が up/down を実行する
   - T2: `MigrationTestRunner.run_cycle()` が例外なく完了する

**受入条件**:
- `py_compile migration_test_framework.py` PASS
- T1 / T2 PASS

### Sprint .2 — 既存 migration v32〜v35 retrofit

**担当**: DBA

**作業**:
1. 既存 migration ファイルを確認し、現在の実装構造を Read:
   - `cli/lib/migrations/` 配下の全ファイルをスキャン
   - `up()` / `down()` / `verify()` がない箇所を特定
2. 各 migration に `MigrationBase` 継承 + 3-method を retrofit:
   - v32: `up()` は既存 DDL を使用、`down()` は DROP/ALTER で逆操作、`verify()` は table 存在確認
   - v33: schema_version table の up/down/verify
   - v34: todo_entries chain の up/down/verify
   - v35: plan_registry / task_queue の up/down/verify
3. `test_migration_framework.py` に v32〜v35 の `run_cycle()` test を追加 (T3〜T6)

**受入条件**:
- T3〜T6 (v32〜v35 cycle) 全件 PASS
- 既存 `helix db migrate` (引数なし) の動作が regression しない

### Sprint .3 — CLI 拡張 + v36 + 全体検証

**担当**: SE + QA

**作業**:
1. `cli/helix-db` (または `cli/helix db` subcommand) に `--dry-run` / `--verify` / `--rollback` 追加
2. PLAN-116 の v36 migration を `MigrationBase` 継承で新規実装
3. `test_migration_framework.py` に T7 (v36 cycle) + T8 (`--dry-run` 構文確認) を追加
4. `helix doctor` に `check_migration_coverage` を追加:
   - `cli/lib/migrations/` に `MigrationBase` を継承しない migration がある → warn (P2)
5. 全体 pytest sweep で regression 確認 (`python3 -m pytest cli/lib/tests/ -q`)

**受入条件**:
- T7 / T8 PASS + 全件 (T1〜T8) PASS
- `helix db migrate --dry-run` が exit 0 で構文確認メッセージを出力
- `helix db migrate --rollback` が直前 version に down() して exit 0
- `helix doctor` に `check_migration_coverage` が追加され warn/pass を返す
- pytest 全体 sweep で regression なし

---

## §6. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| 既存 migration に `down()` が実装不可能な変更がある | retrofit で `down()` が空実装になる | `NotImplementedError` を raise + helix doctor の warn 対象にする。完全な rollback が不可能な migration を機械的に識別できる |
| `--rollback` が本番 helix.db で誤実行される | データ損失 | PLAN-086 の `--dev` flag 継承 + 本番 DB での rollback は `HELIX_ALLOW_ROLLBACK_PROD=1` env 必須 (fail-close) |
| v34 の todo_entries chain が複雑で down() 実装が困難 | Sprint .2 遅延 | v34 は `down()` を best-effort 実装 (partial rollback を明示)、`verify()` で確認できる範囲を明記する |
| pytest fixture の tmp db が helix-db.lock と競合 | 並列 test で lock 競合 | `create_test_db()` は必ず tmpdir に isolation した DB を生成 (`cli/lib/tests/conftest.py` の pattern に準拠、PLAN-100 Phase 4 carry で確立済) |
| PLAN-116 v36 migration が本 PLAN Sprint .3 時点で未完成 | T7 実装が blocking される | T7 は PLAN-116 完了を requires として skip flag を設定、Sprint .3 で条件付き実行 |

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
