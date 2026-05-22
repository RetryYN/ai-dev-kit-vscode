---
plan_id: PLAN-195
title: "PLAN-195: helix.db read replica framework (WAL mode + read connection 分離)"
layer: L4
kind: refactor
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
    slot_label: "DBA — WAL mode 設定 + read-only connection pool 設計 + helix_db_replica.py 実装"
  - role: se
    slot_label: "SE — writer/reader 切り替えロジック統合 + 既存呼び出し箇所 migration + pytest"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-116 / PLAN-185 との設計整合確認・read path 分離範囲チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・WAL 設計 review・regression リスク評価"
generates:
  - artifact_path: docs/plans/PLAN-195-helix-db-read-replica.md
    artifact_type: design_doc
  - artifact_path: cli/lib/helix_db_replica.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_helix_db_replica.py
    artifact_type: test
dependencies:
  parent: PLAN-116
  requires:
    - PLAN-116
    - PLAN-185
  blocks: []
related_adr: []
related_plans:
  - PLAN-116 (helix.db v36 schema — 同一 DB file に対する schema 設計の正本)
  - PLAN-185 (helix.db ACID transaction framework — write path lock 競合解消と本 PLAN read path 分離が補完)
test_design: docs/v2/L4-test-design/PLAN-195-unit-test-design.md (別 session 起票予定)
---

# PLAN-195: helix.db read replica framework

> **位置付け**: helix.db の read-heavy workload 競合を WAL mode + read connection 分離で解消する。
> PLAN-116 (v36 schema) を前提とし、PLAN-185 (ACID transaction) と write path を共有する。

## 1. 目的

helix.db は SQLite single file。`helix metrics` / `helix log report` / `helix code stats` 等の
read-heavy コマンドが write と同時実行されると read が write lock でブロックされる。本 PLAN は:

1. **WAL mode 有効化** — writer と reader が並列動作できる WAL journal mode を適用
2. **read-only connection pool** — read 専用 connection を `helix_db_replica.py` で管理
3. **writer/reader 切り替え API** — 呼び出し側が意図を明示できる context manager を提供

## 2. 背景

### 2.1 PLAN-185 との責務分離

```
write path: PLAN-185 (ACID transaction)  → helix_db.py writer connection
read  path: 本 PLAN (WAL + replica pool) → helix_db_replica.py reader connection
```

### 2.2 WAL mode の制約

- WAL mode は `PRAGMA journal_mode=WAL` で有効化 (DB file ごとに永続化)
- `-shm` / `-wal` の 2 ファイルが DB と同ディレクトリに生成される
- NFS 等のネットワーク fs では動作しない (local fs のみ対象)
- long-running reader がいる場合 WAL file が肥大化する可能性あり (checkpoint 監視推奨)

## 3. 設計方針

### 3.1 helix_db_replica.py の主要 API

```python
class ReadReplicaPool:
    def __init__(self, db_path: str, pool_size: int = 3): ...
    @contextmanager
    def reader(self) -> sqlite3.Connection:
        """with pool.reader() as conn: パターン。URI mode=ro で read-only 接続。"""
        ...

def enable_wal(db_path: str) -> None:
    """PRAGMA journal_mode=WAL を idempotent 適用。"""
    ...
```

### 3.2 呼び出し側の変更方針

read-heavy コマンド 4 件 (`helix metrics` / `log report` / `code stats` / `plan list`) を
`helix_db.connect()` から `ReadReplicaPool.reader()` に切り替える。
write が混在するコマンドは従来通り `helix_db.connect()` (writer) を使用する。

### 3.3 WAL mode 有効化タイミング

- `helix db wal-enable` サブコマンドで手動適用 (または `helix db migrate` 時に自動適用)
- `helix db wal-status` で現在の journal mode を表示

## 4. 実装 Sprint

**Sprint .1** (dba): `helix_db_replica.py` 新規作成 + `enable_wal()` 実装 + py_compile PASS
- ReadReplicaPool (acquire/release/reader context manager)
- URI read-only 接続 (`file:path?mode=ro&uri=true`)
- `helix db wal-enable` / `wal-status` サブコマンド追加

**Entry**: PLAN-116 migration 適用済み / **Exit**: py_compile PASS + enable_wal 動作確認

**Sprint .2** (se): read-heavy コマンド 4 件の reader 切り替え
- `helix metrics` / `log report` / `code stats` / `plan list` の DB 接続変更 (最小変更)

**Entry**: Sprint .1 完遂 / **Exit**: WAL mode 下で read lock なし動作確認

**Sprint .3** (se + pmo-sonnet): pytest + review + G4
- `test_helix_db_replica.py`: enable_wal idempotent / ReadReplicaPool CRUD /
  read-only write → OperationalError / writer-reader 並列動作 / pool_size 超過 blocking
- pmo-sonnet: PLAN-116/185 整合確認 / tl-advisor: G4 凍結判定

**Entry**: Sprint .2 完遂 / **Exit**: pytest 全 PASS + 全回帰 PASS + G4 passed

## 5. DoD

- [ ] `cli/lib/helix_db_replica.py` 実装済み (ReadReplicaPool / enable_wal)
- [ ] WAL mode idempotent 確認 (2 回 `PRAGMA journal_mode=WAL` → 同一結果)
- [ ] `helix db wal-enable` / `wal-status` 動作確認
- [ ] read-heavy コマンド 4 件の reader 切り替え完了
- [ ] `test_helix_db_replica.py` 全 PASS (idempotent / CRUD / OperationalError / 並列)
- [ ] `python3 -m py_compile` + 全回帰 PASS (`helix test`)
- [ ] pmo-sonnet review 承認 / tl-advisor G4 passed

## 6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-195-helix-db-read-replica.md |
| ② 実装コード | 未着手 | cli/lib/helix_db_replica.py |
| ③ テスト設計 | 未起票 | docs/v2/L4-test-design/PLAN-195-unit-test-design.md |
| ④ テストコード | 未着手 | cli/lib/tests/test_helix_db_replica.py |

双方向 reference: 本 PLAN → PLAN-116 (parent) / PLAN-185 (requires)。
実装コード → 本 PLAN: docstring に `# 契約: PLAN-195 §3` を明示 (実装時)。

## 7. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-116 (親 PLAN、v36 schema) | docs/plans/PLAN-116-helix-db-v36-schema.md |
| PLAN-185 (ACID transaction、write path 補完) | docs/plans/PLAN-185-helix-db-acid-transaction.md |
