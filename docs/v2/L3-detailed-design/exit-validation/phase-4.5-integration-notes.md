---
title: "Phase 4.5: 既存ソース活用余地 integration notes (L4 着手前 P0 解消マップ)"
plan_id: PLAN-070
phase: Phase 4.5
created: 2026-05-16
status: ready_for_l4
related:
  - docs/plans/PLAN-070-l3-schema-and-contract-design.md (frozen)
  - docs/plans/PLAN-071-carry-capability-detailing.md (draft)
  - docs/v2/L3-detailed-design/D-API/D-API-draft.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-draft.md
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md
input_reports:
  - /tmp/phase-4.5-A-migration-pattern.md
  - /tmp/phase-4.5-B-cli-hooks.md
  - /tmp/phase-4.5-C-test-fixture.md
  - /tmp/phase-4.5-D-python-helper.md
---

# Phase 4.5: 既存ソース活用余地 integration notes

## TL;DR (5 行以内)

CURRENT_SCHEMA_VERSION=23。v24-v27 の新テーブル 4 本に対して P0 が 9 件確定した。
「3 つの新規 helper 未実装 (P0-01〜03)」「push_gate.py シグネチャ未確認 (P0-04)」が最重要ブロッカー。
migration は v23 の additive pattern を踏襲し、BEFORE UPDATE/DELETE trigger は新規実装が必要。
test fixture は _build_legacy_vNN_db + pytest.raises(IntegrityError) の 2 点セットを全 v24-v27 に適用。
P0 全 9 件を Phase 5 着手前（L4 実装着手チェックリスト通過時）に解消すること。

---

## 1. P0 一覧 (L4 着手前 必須対処、計 9 件)

### P0-01

- **ID**: P0-01
- **source**: D
- **title**: `_upsert_row` helper 未実装
- **内容**: `session_id UNIQUE` 制約に対応する `ON CONFLICT(col) DO UPDATE SET ...` を行う汎用 UPSERT helper が存在しない。既存 `insert_row` は INSERT OR IGNORE 相当で代替不可。
- **対処方針**: Phase 5 着手前に `_upsert_row(conn, table, data, conflict_column)` を `helix_db.py` に新規実装する。
- **関連 file**: `cli/lib/helix_db.py` (L1594 の `insert_row` を参考に実装)

### P0-02

- **ID**: P0-02
- **source**: D
- **title**: `_transition_lifecycle_status` helper 未実装
- **内容**: `automation_runs` の `running → completed / failed / cancelled` lifecycle 遷移を管理する汎用 helper が存在しない。既存 `historical_to_active_audit_decision` は降格専用で汎用性なし。
- **対処方針**: Phase 5 着手前に `_transition_lifecycle_status(conn, table, row_id, from_status, to_status, allowed_transitions)` を新規実装する。
- **関連 file**: `cli/lib/helix_db.py` (L2146 の `historical_to_active_audit_decision` を参考)

### P0-03

- **ID**: P0-03
- **source**: D + A
- **title**: `_create_append_only_trigger` helper 未実装
- **内容**: `automation_runs` (v25) および `audit_log` (v26) の append-only 保証に必要な BEFORE UPDATE / BEFORE DELETE trigger 生成 helper が存在しない。レポート A §3 により既存 trigger 実装例はゼロ。レポート A §5.3 が trigger 方式 (P1) と voided_at 方式 (推奨) を示すが、P0-03 は「trigger を使う場合の実装不在」として明示。
- **対処方針**: **TL 判定済 (2026-05-16 Codex tl-advisor): hybrid 採用**
  - **v26 audit_log**: trigger 方式 (方式 B) で物理 UPDATE/DELETE 拒否、`CREATE TRIGGER IF NOT EXISTS` で idempotent 化
  - **v25 automation_runs**: lifecycle helper (`_transition_lifecycle_status`) + 限定 trigger (DELETE 禁止 + immutable 列 [id, run_kind, started_at] + terminal final 強制)。terminal 遷移 (running→completed) で UPDATE 必要のため全面拒否しない
  - **理由**: audit_log は監査証跡で物理改ざん耐性必須、automation_runs は lifecycle 遷移で UPDATE 必要のため hybrid
  - **新規 helper**: `_create_append_only_trigger(conn, table_name, immutable_columns=None, terminal_status_column=None, terminal_values=None)` を実装。`IF NOT EXISTS` 必須 / rollback SQL 添付 / pytest `IntegrityError` 固定 (P1-04 統合)
- **関連 file**: `cli/lib/helix_db.py` (L1210 の v23 `voided_at` pattern 参照)

### P0-04

- **ID**: P0-04
- **source**: B
- **title**: `push_gate.py` の `run_all_gates()` シグネチャ未確認
- **内容**: `helix-pr` L147-153 が `inspect.signature(run_all_gates).parameters` で動的にキーワード引数を確認している。`push_trigger` / `pr_trigger` endpoint を設計する前に `push_gate.py` の `run_all_gates()` シグネチャ（引数名 / 戻り値型）を実際に Read して確認する必要がある。本調査スコープ外のため未確認。
- **対処方針**: Phase 5 着手前に `cli/lib/push_gate.py` を Read し、シグネチャと戻り値型を D-API / D-CONTRACT に反映する。
- **関連 file**: `cli/helix-pr` (L107-191), `cli/lib/push_gate.py` (未読、P0 対処として Read 必須)

### P0-05

- **ID**: P0-05
- **source**: A
- **title**: v24 `design_sprint_drive_decisions` — `_has_table` guard 漏れリスク
- **内容**: レポート A §5.1 より、v20 の `if not _has_table(...): executescript(...)` パターンを必ず踏襲する必要がある。guard 漏れが発生すると migration が既存 DB に対して二重実行され、テーブル破損を招く。
- **対処方針**: Phase 5 実装時に `_migrate_v23_to_v24(conn)` 内で `_has_table(conn, "design_sprint_drive_decisions")` guard を冒頭に配置することを委譲 prompt に明示する。
- **関連 file**: `cli/lib/helix_db.py` (L1111-1115 の v20 `_has_table` guard pattern)

### P0-06

- **ID**: P0-06
- **source**: A
- **title**: v25 `automation_runs` — CHECK constraint は CREATE TABLE 時のみ有効
- **内容**: レポート A §5.2 より、`status TEXT NOT NULL CHECK(status IN (...))` は `ADD COLUMN` への追記では SQLite runtime 依存で動作しないことが v21 コメント (L1169-1170) で明示されている。CREATE TABLE 時に埋め込む必要がある。
- **対処方針**: Phase 5 実装時に `AUTOMATION_RUNS_SCHEMA_V25` 定数を定義し、CREATE TABLE 文の中に CHECK を直接記述する。ADD COLUMN での CHECK 追加は禁止。
- **関連 file**: `cli/lib/helix_db.py` (L1169-1170 の v21 警告コメント)

### P0-07

- **ID**: P0-07
- **source**: C
- **title**: `CURRENT_SCHEMA_VERSION` を 27 に更新後、既存 3 ファイルの assert を一括更新しないと CI 失敗
- **内容**: レポート C §4 P0-1 より、`test_helix_db_v19.py` / `test_helix_db_v22.py` / `test_helix_db_v23.py` の 3 ファイルに `assert helix_db.CURRENT_SCHEMA_VERSION == 23` が残存している。v27 更新後は全てを 27 に連動更新しないと CI 4 件が失敗する（過去 CI 失敗事例: memory `feedback_codex_migration_test_version_drift.md`）。
- **対処方針**: Phase 5 委譲 prompt に「全ファイルの `CURRENT_SCHEMA_VERSION == XX` を grep し一括更新する」を明示する。
- **関連 file**: `cli/lib/tests/test_helix_db_v19.py`, `test_helix_db_v22.py`, `test_helix_db_v23.py`

### P0-08

- **ID**: P0-08
- **source**: C
- **title**: FK 検証テストで `PRAGMA foreign_keys = ON` 漏れリスク
- **内容**: レポート C §4 P0-3 より、FK constraint は `PRAGMA foreign_keys = ON` を明示しないと素通りになる。v24 の `source_entry_id → design_sprint_entries(id)` FK、v26 の `run_id → automation_runs(id)` FK はいずれも FK 検証テストを持つ予定。
- **対処方針**: Phase 5 の新規テストファイル (`test_helix_db_v24.py` 等) の先頭に `conn.execute("PRAGMA foreign_keys = ON")` を必須パターンとして記載することを委譲 prompt に明示する。
- **関連 file**: `cli/lib/tests/test_helix_db_v24.py` (新規作成予定)

### P0-09

- **ID**: P0-09
- **source**: A + D
- **title**: `migrate()` 関数への v24-v27 分岐追記を忘れると新 migration が発火しない
- **内容**: レポート A §2 の各 `_migrate_vNN_to_vMM` は `migrate()` (L1414) 内の `if current_version < MM:` 分岐に登録されて初めて機能する。4 関数すべてを `migrate()` に追記しないと DB が v23 のまま初期化される。
- **対処方針**: Phase 5 委譲 prompt に「`migrate()` 関数内の v24/v25/v26/v27 分岐を追加する」を明示し、実装後に `SELECT MAX(version) FROM schema_version` で 27 を確認するテストを追加する。
- **関連 file**: `cli/lib/helix_db.py` (L1414 の `migrate()` 分岐)

---

## 2. P1 一覧 (Phase 5 内で拾うべき、見落とすと implementation drift)

### P1-01

- **ID**: P1-01
- **source**: B
- **title**: `hook_callback` endpoint と `invocation_log` の型衝突リスク
- **内容**: 既存 hook は `invocation_log.type = "hook"` を固定値として書き込んでいる。`hook_callback` endpoint から `"push_trigger"` / `"hook_callback"` 等の値を同テーブルへ書き込むと `pretooluse-askuserquestion.sh` の `role=tl-advisor` フィルタに影響が出る可能性がある。
- **対処方針**: Phase 5 内で `session_telemetry` / `audit_log` テーブルを新規エンドポイントの書き込み先とし、`invocation_log` には書き込まない設計を D-CONTRACT で確定する。
- **関連 file**: `.claude/hooks/pretooluse-askuserquestion.sh` (L52-68), D-CONTRACT-draft.md

### P1-02

- **ID**: P1-02
- **source**: B
- **title**: `HELIX_DIR` 解決経路が hook プロセスと endpoint プロセスで乖離する可能性
- **内容**: hook は `source helix-common.sh` 経由で `HELIX_DIR` を解決するが、HTTP server は別プロセスから起動するため同じパスを指す保証がない。`resolve_default_db_path()` を共通化すれば統一できるが、Phase 5 実装時に明示注入を忘れると DB パスが乖離する。
- **対処方針**: Phase 5 実装時に endpoint 起動スクリプトに `HELIX_DIR` の明示注入を追加するか、`helix_db.resolve_default_db_path()` を呼び出す共通エントリポイントを設ける。
- **関連 file**: `cli/lib/helix_db.py` (L1583 の `resolve_default_db_path`), `.claude/hooks/post-tool-use.sh` (L11)

### P1-03

- **ID**: P1-03
- **source**: D
- **title**: `_validate_positive_number` (float 対応) が未実装
- **内容**: v27 `session_telemetry.cost_usd` は float 型だが、既存 `_validate_positive_int` は int 限定で float 非対応。`cost_usd` へのバリデーションが省略または不正確になるリスク。
- **対処方針**: Phase 5 内で `_validate_positive_number(value, field_name)` を追加するか、`cost_usd` を TEXT として保存し app-layer で変換する設計を TL が選択する。
- **関連 file**: `cli/lib/helix_db.py` (L1885 の `_validate_positive_int`)

### P1-04

- **ID**: P1-04
- **source**: A
- **title**: v26 `audit_log` の trigger 方式採用時に idempotent 作成が必要
- **内容**: trigger を新規実装する場合は `CREATE TRIGGER IF NOT EXISTS` で idempotent に作成し、`_has_table` guard の後に呼ぶ必要がある。既存に trigger 実装例がないため、migration 関数内での配置ルールが未確立。
- **対処方針**: P0-03 の TL 判定で trigger 方式を採用した場合、Phase 5 実装時に trigger 作成を `_migrate_v25_to_v26` に `IF NOT EXISTS` で追記する。
- **関連 file**: `cli/lib/helix_db.py` (新規 `_migrate_v25_to_v26` 内)

### P1-05

- **ID**: P1-05
- **source**: C
- **title**: `test_v24_to_v27_sequential_migration` 連鎖テストが未起票
- **内容**: v24 DB から `migrate()` を呼んで `schema_version` に `[24,25,26,27]` が登録されることを確認する連鎖テストが必要。既存は `test_migrate_v19_to_current` (v19→v23) が参考例。
- **対処方針**: Phase 5 内の `test_helix_db_v27.py` または新規テストファイルに追加する。G4 前に揃えること。
- **関連 file**: `cli/lib/tests/test_helix_db_v20.py` (参考: `test_migrate_v19_to_current`)

---

## 3. v24 design_sprint_drive_decisions 実装ガイド

### 3.1 流用 migration pattern (source: A §5.1)

```python
def _migrate_v23_to_v24(conn: sqlite3.Connection) -> None:
    """v24: design_sprint_drive_decisions テーブル追加"""
    if not _has_table(conn, "design_sprint_drive_decisions"):
        conn.executescript(DESIGN_SPRINT_DRIVE_DECISIONS_SCHEMA_V24)
```

- `_has_table` guard は v20 パターン (A §2, L1111-1115) を踏襲する
- CHECK constraint は CREATE TABLE の DDL に直接埋め込む (v21 ADD COLUMN 警告回避)
- FK `source_entry_id / target_entry_id → design_sprint_entries(id)` は v21 で作成済みの FK 先を直接参照可

### 3.2 流用 helper 関数 (source: D §4.1)

| 操作 | 使用 helper | 流用スコア |
|------|------------|-----------|
| INSERT | `insert_row(db_path, "design_sprint_drive_decisions", data)` | high |
| enum validation | `_validate_choice(value, allowed, field_name)` | high |
| 存在確認 | `_has_table(conn, table_name)` | high |
| 接続取得 | `get_connection(db_path)` | high |

### 3.3 必須 test fixture (source: C §3.1)

- `_build_v23_db(db_path)` — v23 まで手組みして test DB を構築 (C §3.1 の雛形を使用)
- 必須 test case:
  1. `test_v23_to_v24_migrate_succeeds` — テーブル存在 + 必須列 (decision_type / source_entry_id FK)
  2. `test_v24_migrate_is_idempotent` — `init_db × 2` で version=24 が 1 行のみ
  3. `test_v24_decision_enum_check` — `pytest.raises(IntegrityError)` で無効 decision_type
  4. `test_v24_source_entry_id_fk` — `PRAGMA foreign_keys = ON` + 存在しない FK で IntegrityError

### 3.4 検証手順

```bash
python3 -m pytest cli/lib/tests/test_helix_db_v24.py -v
python3 -c "import cli.lib.helix_db as h; print(h.CURRENT_SCHEMA_VERSION)"  # 出力: 27
```

---

## 4. v25 automation_runs 実装ガイド

### 4.1 流用 migration pattern (source: A §5.2)

```python
AUTOMATION_RUNS_SCHEMA_V25 = """
CREATE TABLE IF NOT EXISTS automation_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_kind        TEXT NOT NULL,
    plan_id         TEXT,
    trigger_actor   TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    ended_at        TEXT,
    status          TEXT NOT NULL CHECK(status IN ('pending','running','completed','failed','cancelled')),
    exit_code       INTEGER,
    summary         TEXT,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT
);
"""

def _migrate_v24_to_v25(conn: sqlite3.Connection) -> None:
    if not _has_table(conn, "automation_runs"):
        conn.executescript(AUTOMATION_RUNS_SCHEMA_V25)
```

- `status` の CHECK は CREATE TABLE 時に埋め込む (A §5.2 P0 / v21 警告回避)
- `retry_count / max_retries / last_error` は v9 `jobs` テーブル (A §4) から直接流用

### 4.2 lifecycle 強制方法 (source: A §4 + P0-03 hybrid 判定 2026-05-16)

- DB レベルの terminal status 強制: CHECK constraint (CREATE TABLE 時埋め込み)
- app-layer の遷移制御: P0-02 の `_transition_lifecycle_status` helper で実装
- **BEFORE UPDATE / DELETE trigger による append-only 強制 (hybrid 限定 trigger 採用)**:
  - DELETE 禁止: `BEFORE DELETE ON automation_runs BEGIN SELECT RAISE(ABORT, 'automation_runs is append-only'); END`
  - immutable 列 (id / run_kind / started_at): `BEFORE UPDATE OF id, run_kind, started_at ...`
  - terminal final 強制: `BEFORE UPDATE WHEN OLD.status IN ('completed','failed','cancelled')` で UPDATE 拒否
  - status `pending → running → terminal` の正規遷移は `_transition_lifecycle_status` helper 経由 (app-layer check)

### 4.3 流用 helper 関数 (source: D §4.2)

| 操作 | 使用 helper | 流用スコア |
|------|------------|-----------|
| append-only INSERT | `insert_row(db_path, "automation_runs", data)` | high |
| status enum validation | `_validate_choice(value, ALLOWED_STATUSES, "status")` | high |
| lifecycle 遷移 | `_transition_lifecycle_status(...)` — P0-02 新規実装 | P0 必須 |
| trigger 生成 | `_create_append_only_trigger(conn, "automation_runs")` — P0-03 | P0-03 判定次第 |

### 4.4 必須 test fixture (source: C §3.2)

- 参考: `test_helix_db.py` の `_insert_import_run_direct` + `test_import_runs_status_check_constraint`
- 必須 test case:
  1. `test_v24_to_v25_migrate_succeeds` — テーブル存在 + 必須列
  2. `test_v25_terminal_status_is_immutable` — terminal status 行への UPDATE が IntegrityError (C §3.2 雛形)
  3. `test_v25_append_only_insert_only` — terminal status 行への再 INSERT が拒否
  4. `test_v25_lifecycle_valid_transitions` — 無効 status 遷移が IntegrityError

### 4.5 既存 cli/helix-push との overlap 対処 (source: B §4.1)

- `helix-push` 本体 (83 行) は `push_gate.py` への thin wrapper。helix.db への直接書き込みなし。
- `push_trigger` endpoint は `push_gate.run_all_gates()` を直接呼ぶか subprocess として起動する。
- `automation_runs` への書き込みは endpoint 側で行い、`helix-push` 本体は変更しない。
- P0-04 (push_gate.py シグネチャ確認) 解消後に endpoint 設計を確定する。

---

## 5. v26 audit_log 実装ガイド

### 5.1 append-only trigger pattern (source: A §3 + §5.3 + P0-03 hybrid 判定 2026-05-16)

**TL 判定結果 (2026-05-16 Codex tl-advisor)**: **方式 2 (trigger 方式) 採用**

理由: audit_log は監査証跡で物理改ざん耐性必須。voided_at 方式 (論理無効化) では監査ログの物理 UPDATE を防げない。

**実装**:
- `_create_append_only_trigger(conn, "audit_log", immutable_columns=["payload"])` を呼び、以下 2 trigger を生成:
  - `BEFORE UPDATE OF payload ON audit_log BEGIN SELECT RAISE(ABORT, 'audit_log.payload is immutable'); END`
  - `BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END`
- `CREATE TRIGGER IF NOT EXISTS` で idempotent 化 (P1-04 統合)
- rollback SQL: `DROP TRIGGER IF EXISTS audit_log_payload_immutable; DROP TRIGGER IF EXISTS audit_log_no_delete;`
- pytest: `pytest.raises(sqlite3.IntegrityError, match="immutable")` で物理 UPDATE/DELETE 拒否を確認

### 5.2 既存 invocation_log との型衝突対処 (source: B §4.3 P1-1)

- `audit_log` テーブルは `invocation_log` とは完全分離で設計する。
- 既存 hook からの `invocation_log` への書き込みは変更しない。
- `audit_log.run_id → automation_runs(id)` FK を持ち、`invocation_log` には依存しない。

### 5.3 流用 helper 関数 (source: D §4.3)

| 操作 | 使用 helper | 流用スコア |
|------|------------|-----------|
| append-only INSERT | `insert_row` / `insert_audit_decision` pattern (L2085) | high |
| audit_kind enum validation | `_validate_choice` | high |
| run_id FK チェック | `_require_non_empty` + `_has_table` | high |
| payload JSON 正規化 | `_json_text` (既存確認要) | high |
| DELETE / UPDATE trigger | `_create_append_only_trigger` — P0-03 | P0-03 判定次第 |

### 5.4 必須 test fixture (source: C §3.3)

- 参考: `test_helix_db.py` の `test_audit_decisions_*` 系
- 必須 test case:
  1. `test_v25_to_v26_migrate_succeeds` — テーブル存在 + payload / recorded_at 列
  2. `test_v26_payload_immutable` — payload への UPDATE が RAISE(ABORT) (C §3.3 雛形)
  3. `test_v26_payload_not_null` — payload=NULL INSERT で IntegrityError
  4. `test_v26_audit_log_fk_to_task_runs` — 存在しない run_id で IntegrityError (foreign_keys=ON 必須)

---

## 6. v27 session_telemetry 実装ガイド

### 6.1 UNIQUE constraint pattern (source: A §5.4)

- 流用元: v20 `test_baseline (UNIQUE (commit_sha, suite, test_name))` および v10 `CREATE UNIQUE INDEX` (後付け例)
- 推奨: CREATE TABLE 時に `session_id TEXT NOT NULL UNIQUE` を埋め込む (migration 時の後付け index より安全)
- `sessions(id)` FK: v16 で作成済み `sessions.id TEXT PRIMARY KEY` を REFERENCES で参照可 (A §5.4 P2)

### 6.2 流用 helper 関数 (source: D §4.4)

| 操作 | 使用 helper | 流用スコア |
|------|------------|-----------|
| UPSERT (session_id 重複時) | `_upsert_row(conn, table, data, "session_id")` — P0-01 新規実装 | P0 必須 |
| nullable FK (related_plan_id) | `_validate_optional_choice` pattern (L1891) | med (参考流用) |
| cost_usd バリデーション | `_validate_positive_number` — P1-03 新規実装 | P1 |
| 接続取得 | `get_connection(db_path)` | high |

### 6.3 既存 hook telemetry channel との統合 (source: B §3 + §4.3)

- 既存 `post-tool-use.sh` / `stop.sh` は `invocation_log` に書き込む。
- `session_telemetry` への書き込みは新規 endpoint (`hook_callback` 相当) 経由とし、既存 hook script は変更しない。
- P1-02 (HELIX_DIR 解決) を Phase 5 実装時に対処すること。

### 6.4 必須 test fixture (source: C §3.4)

- 必須 test case:
  1. `test_v26_to_v27_migrate_succeeds` — テーブル存在 + session_id / started_at 列
  2. `test_v27_session_id_unique` — 同一 session_id 2 回 INSERT で IntegrityError (C §3.4 雛形)
  3. `test_v27_session_id_not_null` — session_id=NULL で IntegrityError
  4. `test_v27_migrate_is_idempotent` — `init_db × 2` で version=27 が 1 行のみ

---

## 7. 全 v24-v27 共通の HELIX_DIR 解決経路統一 (source: B §5 P1-2)

**問題**: hook プロセス (`source helix-common.sh` 経由) と HTTP endpoint プロセスで `HELIX_DIR` 解決経路が乖離する可能性がある。

**対処方針**:
1. 全 migration 関数および endpoint が `helix_db.resolve_default_db_path()` (L1583) を呼ぶことを統一ルールにする。
2. endpoint 起動スクリプトに `HELIX_DIR` 明示注入を追加する。
3. テスト時は `tmp_path / ".helix" / "helix.db"` をハードコードし環境変数の影響を排除する (既存 pytest pattern 踏襲)。

**検証**: bats テストで `HELIX_PROJECT_ROOT` を明示設定した上で endpoint を起動し、同一 DB パスに書き込まれることを確認する。

---

## 8. Phase 5 (L4 実装) 着手チェックリスト

L4 実装着手前に以下の全 P0 が解消済みであることを確認する。実装担当 (Codex SE) はこのチェックリストを参照して実装を開始すること。

- [ ] P0-01: `_upsert_row(conn, table, data, conflict_column)` を `helix_db.py` に新規実装済み
- [ ] P0-02: `_transition_lifecycle_status(conn, table, row_id, from_status, to_status, allowed_transitions)` を `helix_db.py` に新規実装済み
- [x] P0-03: TL 判定済 (2026-05-16): **hybrid 採用** (v26 audit_log=trigger 方式 / v25 automation_runs=lifecycle helper + 限定 trigger)。`_create_append_only_trigger(conn, table_name, immutable_columns=None, terminal_status_column=None, terminal_values=None)` を Phase 5 で新規実装する
- [x] P0-04: `cli/lib/push_gate.py` を Read し `run_all_gates()` のシグネチャと戻り値型を D-API / D-CONTRACT に反映済み (commit-pending) — 2026-05-16
- [ ] P0-05: `_migrate_v23_to_v24` 内に `_has_table(conn, "design_sprint_drive_decisions")` guard を配置することを委譲 prompt に明記済み
- [ ] P0-06: `AUTOMATION_RUNS_SCHEMA_V25` 定数を定義し、CHECK constraint を CREATE TABLE DDL に直接記述することを委譲 prompt に明記済み
- [ ] P0-07: `CURRENT_SCHEMA_VERSION` を 27 に更新する際に `test_helix_db_v19.py` / `v22.py` / `v23.py` の assert を一括更新することを委譲 prompt に明記済み
- [ ] P0-08: 新規テストファイルに `conn.execute("PRAGMA foreign_keys = ON")` を必須パターンとして記載することを委譲 prompt に明記済み
- [ ] P0-09: `migrate()` 関数 (L1414) に v24 / v25 / v26 / v27 の 4 分岐を追記することを委譲 prompt に明記済み

---

## 9. PLAN-070 / draft への反映項目 (frozen のため amendment 形式)

PLAN-070 は G3 凍結済みのため直接修正は行わない。本 integration_notes が **後段 amendment** として機能する。

以下の事項は PLAN-070 draft の想定から変更または補足が必要な内容として記録する:

| 項目 | PLAN-070 draft の想定 | amendment 内容 | 根拠 |
|------|---------------------|---------------|------|
| append-only 実装方式 | 未確定 | trigger 方式と voided_at 方式の 2 択を P0-03 として TL 判定に委ねる | A §3, D §4.3 |
| `push_gate.py` 戻り値型 | 未調査 | P0-04 として Phase 5 前に Read 必須 | B §5 P0-1 |
| `_upsert_row` helper | 未実装 | P0-01 として新規実装が必要 | D §5, §6 |
| `_transition_lifecycle_status` | 未実装 | P0-02 として新規実装が必要 | D §5, §6 |
| `CURRENT_SCHEMA_VERSION` 更新時の連動 | 言及なし | P0-07 として 3 ファイル一括更新を委譲 prompt に明記 | C §4 P0-1 |
| `HELIX_DIR` 解決統一 | 未言及 | §7 の統一方針を L4 実装ガイドに追加 | B §5 P1-2 |

---

## 10. PLAN-071 (carry capability) への波及

PLAN-071 (carry capability detailing) との接点:

- P0-01 (`_upsert_row`): session_telemetry の carry 集計に UPSERT が必要になる可能性がある。PLAN-071 設計時に `session_id` の上書き更新 vs 新規 INSERT を確定すること。
- P0-02 (`_transition_lifecycle_status`): automation_runs の lifecycle が carry 状態管理と連携する場合、allowed_transitions の定義を PLAN-071 の carry ステータス遷移と整合させること。
- P1-01 (invocation_log 型衝突): PLAN-071 が carry event を `invocation_log` へ書く設計にした場合、type フィールドの値域を事前に確定すること。
- P1-03 (`_validate_positive_number`): PLAN-071 で cost_usd のキャリーオーバー計算が必要な場合、float 精度の扱いを統一すること。

## Sprint .5 Resolution Note

- `invocation_log` は LLM 委譲呼び出し専用とし、Claude hook 実行 (`stop.sh` / `post-tool-use.sh`) は今後 `audit_log` のみへ記録する。
- `audit_log` は hook / gate / endpoint / CLI の汎用監査証跡とし、`run_id` は `automation_runs.id` の FK として扱う。
- `helix-push` / `helix-pr` は `HELIX_AUTOMATION_RUN_ID` を子プロセスへ export し、hook 側は同 env var を `audit_log.run_id` に伝播する。
- DB パス解決は hook / endpoint ともに `helix_db.resolve_default_db_path()` を正本にする。

---

## 11. 次 step

1. **即時 (Phase 5 着手前)**: TL が P0-03 (trigger vs voided_at) の方式を確定する → `helix codex --role tl-advisor --task "v25/v26 append-only 方式判定"` で相談
2. **即時**: P0-04 として `cli/lib/push_gate.py` を Read し `run_all_gates()` シグネチャを D-API / D-CONTRACT へ反映
3. **Phase 5 委譲 prompt 準備**: P0-01 / P0-02 / P0-03(確定後) の 3 helper を 1 Sprint で先行実装し、その後 v24→v27 migration を順次実装する
4. **Phase 5 委譲 prompt 必須明記事項**:
   - `migrate()` v24-v27 分岐追記
   - `_has_table` guard 全 migration 関数に配置
   - CHECK constraint は CREATE TABLE DDL のみ (ADD COLUMN 禁止)
   - `CURRENT_SCHEMA_VERSION == 23` の全 grep → 27 一括更新
   - `PRAGMA foreign_keys = ON` を FK テスト全ケースに記載
5. **G4 前**: P1-05 (`test_v24_to_v27_sequential_migration`) を追加してから G4 gate を通す
