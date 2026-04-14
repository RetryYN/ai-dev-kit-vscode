# D-DB-MIGRATION: DB マイグレーション戦略

> Status: Accepted
> Date: 2026-04-14
> Authors: TL

---

## 1. 目的

HELIX CLI の SQLite データベース（`.helix/helix.db`）は運用中にスキーマ変更が発生する。本文書は:

- 現在までのマイグレーション履歴（v1〜v4）
- 次回 v5 以降を追加する手順
- 互換性とロールバック方針

を定義する。GAP-024「DB マイグレーション戦略の文書なし」の解消を目的とする。

---

## 2. 実装アーキテクチャ

### 2.1 バージョン管理テーブル

マイグレーション状態は `schema_version` テーブルで追跡する:

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

各マイグレーション関数は INSERT OR IGNORE で自身のバージョンを記録する。

### 2.2 マイグレーション実行フロー

```python
# cli/lib/helix_db.py
def init_db(db_path):
    conn = _connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # FK 制約を有効化
    _ensure_schema(conn)                       # スキーマ初期化
    conn.commit()
    conn.close()

def _ensure_schema(conn):
    conn.executescript(SCHEMA)                 # v1 スキーマ適用
    conn.executescript(SCHEMA_VERSION_SCHEMA)  # schema_version テーブル作成
    migrate(conn)                              # 必要なマイグレーション実行

def migrate(conn):
    current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
    if current < 2:
        _create_requirements_tables(conn)
        # INSERT OR IGNORE into schema_version (version=2)
    if current < 3:
        # ... インデックス追加 ...
    if current < 4:
        # ... FK カラム追加 ...
```

### 2.3 設計原則

- **冪等性**: 何度実行しても安全（INSERT OR IGNORE、CREATE IF NOT EXISTS）
- **逐次適用**: 各バージョンは直前のバージョンを前提にする
- **ロールバックなし**: downgrade はサポートしない（データ損失リスクを避ける）
- **PRAGMA foreign_keys = ON**: 全接続で FK 制約を有効化
- **非破壊**: 既存データを保持する変更のみ（DROP TABLE / DROP COLUMN は避ける）

---

## 3. マイグレーション履歴

### 3.1 v1 → 初期スキーマ

**実装箇所:** `cli/lib/helix_db.py` の `SCHEMA` 定数

**主要テーブル:**

- `task_runs` — タスク実行履歴
- `action_logs` — アクション実行ログ
- `gate_runs` — ゲート実行履歴
- `cost_log` — コスト記録（トークン・モデル）
- `hook_events` — Claude Code hook イベント
- `interrupts` — IIP/CC 割り込み履歴
- `retro_items` — ミニレトロ項目
- `task_observations` — タスク品質観測
- `recipes` — Learning Engine 生成 recipe
- `builder_executions` — Builder 実行履歴
- `builder_history` — Builder 履歴検索用
- `debt_items` — 技術的負債レジスタ

### 3.2 v1 → v2: Requirements テーブル追加

**実装箇所:** `_create_requirements_tables()`

**追加テーブル:**

- `requirements` — 要件管理
- `requirement_links` — 要件→成果物リンク

**背景:** L1 要件管理を SQLite で追跡するため

### 3.3 v2 → v3: パフォーマンスインデックス

**実装箇所:** `migrate()` 内の v2→v3 ブロック

**追加インデックス:**

- `idx_task_runs_task_id_id_desc ON task_runs(task_id, id DESC)`
- `idx_action_logs_task_run_status ON action_logs(action_type, status)`

**背景:** `helix log report` のクエリ性能改善

### 3.4 v3 → v4: Foreign Key カラム追加

**実装箇所:** `_migrate_gate_runs_v4()`, `_migrate_interrupts_v4()`, `_migrate_retro_items_v4()`

**変更:**

- `gate_runs` に `task_run_id INTEGER REFERENCES task_runs(id)` 追加
- `interrupts` に `task_run_id INTEGER REFERENCES task_runs(id)` 追加
- `retro_items` に `gate_name TEXT`, `gate_run_id INTEGER REFERENCES gate_runs(id)` 追加
- FK 用インデックス追加

**テクニック:** SQLite は ALTER TABLE で FK 追加ができないため、以下の手順を採用:

1. 新テーブル（FK 付き）を `<table>_new` として作成
2. 既存データを新テーブルにコピー
3. 旧テーブル DROP
4. 新テーブルを旧名にリネーム

**背景:** GAP-006/007 の FK 整合性強化

---

## 4. 次回 v5 以降の追加手順

### 4.1 手順

1. **設計フェーズ**: 変更内容を D-DB-MIGRATION.md に追記（本文書の §3 に v5 セクション追加）
2. **コード実装**:
   - `helix_db.py` に `_migrate_*_v5()` 関数を追加
   - `CURRENT_SCHEMA_VERSION = 5` に更新
   - `migrate()` 内に `if current < 5:` ブロック追加
   - 末尾で `INSERT OR IGNORE INTO schema_version (version=5)`
3. **テスト実装**:
   - `test_helix_db.py` にマイグレーションテスト追加
   - v4 DB からの upgrade が成功することを確認
   - マイグレーション後の構造を PRAGMA table_info で検証
4. **ドキュメント更新**: 本文書 §3 に v5 セクション追加
5. **検証**: `python3 -m pytest cli/lib/tests/test_helix_db.py -v` 通過

### 4.2 新テーブル追加の雛形

```python
def _migrate_new_feature_v5(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS new_feature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    ''')
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_new_feature_name ON new_feature(name)"
    )

# migrate() 内に追加
if current < 5:
    _migrate_new_feature_v5(conn)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (5, datetime('now'))"
    )
```

### 4.3 既存テーブルの変更（ALTER TABLE）

SQLite の ALTER TABLE は以下のみサポート:

- `ADD COLUMN`（デフォルト値付き）
- `RENAME COLUMN`（3.25.0以降）
- `RENAME TO`

以下は **未サポート** のため、テーブル再作成が必要:

- `DROP COLUMN`
- `ALTER COLUMN TYPE`
- Foreign Key 追加

再作成手順は v3→v4 の `_migrate_gate_runs_v4` を参照。

---

## 5. 互換性方針

| 観点 | 方針 |
|------|------|
| 古い DB からの upgrade | v1 以降の全バージョンから v4 への upgrade を保証 |
| 新しい DB から古い HELIX | サポートしない（前方互換性なし） |
| データ損失 | マイグレーション中のデータ損失は許容されない |
| 実行時間 | 通常サイズの helix.db（< 10MB）で1秒以内 |
| エラー時の挙動 | マイグレーション失敗時は rollback、エラーメッセージで `helix doctor` 実行を推奨 |

---

## 6. テスト戦略

| テスト種別 | 対象 | 実装 |
|----------|------|------|
| 初期化テスト | 新規 DB が v4 スキーマで正しく作成されるか | `test_helix_db.py::test_init_db` |
| アップグレードテスト | v1 DB から v4 へのマイグレーション | `test_helix_db.py::test_migrate_*` |
| FK 制約テスト | PRAGMA foreign_keys = ON が効いているか | `test_helix_db.py::test_fk_constraints` |
| 冪等性テスト | init_db を複数回実行しても壊れないか | `test_helix_db.py::test_idempotent_init` |

---

## 7. 関連ファイル

- `cli/lib/helix_db.py` (844行) — マイグレーション実装本体
- `cli/lib/tests/test_helix_db.py` (438行, 15テスト) — マイグレーションテスト
- [ADR-005: YAML-SQLite Dual State](../adr/ADR-005-yaml-sqlite-dual-state.md) — 状態管理の上位方針
- [L2-cli-architecture.md](./L2-cli-architecture.md) — CLI 全体アーキテクチャ

---

## 8. 既知の制約・今後の課題

| 項目 | 内容 | 優先度 |
|------|------|------|
| downgrade 機能なし | データ損失リスクのため意図的に未実装 | — |
| 大規模 DB での性能 | 100MB 超の DB でのマイグレーション性能未検証 | P3 |
| バックアップ戦略 | マイグレーション前の自動バックアップ未実装 | P2 |
| データ移行ツール | 他形式（PostgreSQL等）への移行ツール未実装 | P3 |
