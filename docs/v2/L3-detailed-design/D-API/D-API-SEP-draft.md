---
doc_id: D-API-SEP-draft-v0.1
plan_id: PLAN-084
sprint: Phase 3 / L3 詳細設計
status: draft
created: 2026-05-17
primary_drive: be
extends: D-API-EXTENDED-draft-v0.1
related_adrs:
  - ADR-018-db-separation-and-event-sourcing
related_plans:
  - PLAN-084
sibling_docs:
  - D-DB-SEP-draft-v0.1 (Phase 3.1 起票済、schema 正本)
  - D-CONTRACT-EVENT-draft-v0.1 (Phase 3.3 起票予定、event envelope 正本)
---

# PLAN-084 Phase 3: L3 D-API 6 分離 compatibility adapter 詳細設計 v0.1

## §1 目的とスコープ

### 1.1 本文書の位置づけ

本文書は ADR-018 §Decision.5 (compatibility adapter) を Python API レベルに展開し、Phase 4.A
実装の正本契約とする L3 詳細設計書である。

D-DB-SEP-draft (Phase 3.1 起票済) が 6 db schema 契約の正本である一方、本文書は
`cli/lib/compatibility_adapter.py` の API 設計 (関数 signature / routing 規則 / dual-write 制御 /
transaction 境界) を確定する。Phase 4.A 実装担当 (Codex se) はこの契約に従って実装し、既存
11 file (lib 8 + top-level CLI 3) × 30+ 箇所の `helix_db._write_connection(None)` 呼び出しを
**API 互換 100% 維持** で 6 db 経路へ adapt する。

### 1.2 スコープ

**In-scope**:

- `cli/lib/compatibility_adapter.py` の Python API 設計 (contextmanager / routing / dual-write / read)
- 11 file 別の 6 db routing 先 + adapter test 観点の契約
- cross-db read helper (`read_cross_db_projection`) の API 設計
- ATTACH 禁止 CI gate の grep コマンド仕様
- `cli/libexec/helix-session-start` が adapter 対象外である根拠の明記
- Phase 4.A / 4.B / 4.C carry 項目の割当

**Non-goals**:

- 6 db schema 詳細 (D-DB-SEP-draft で扱う)
- event envelope の Python class 設計 (D-CONTRACT-EVENT-draft で扱う)
- projector 実装本体 (Phase 4.B、Codex se 担当)
- frontend.db / backend.db state-store の event-sourced 再判定実装 (ADR-018 §Decision.4、6 ヶ月後 review)
- HTTP endpoint 層の新規追加 (D-API-EXTENDED-draft の既存 5 endpoint を継承)

### 1.3 前段文書との接続

| 前段文書 | 接続箇所 |
|---|---|
| ADR-018 §Decision.5 | 本文書全体の根拠。compatibility adapter の責務・dual-write 制御・API 互換 100% 維持要件 |
| ADR-018 §Decision.1 | ATTACH 禁止規約の根拠。本文書 §5 に展開 |
| D-DB-SEP-draft-v0.1 §2-6 | sibling doc。schema 正本、entity ownership 表、migration gate 順序。本文書と双方向 trace |
| L1-REQUIREMENTS.md §3.9 FR-DB-SEP-06 | migration gate 6 段階の受入条件。compatibility adapter は AC-DB-SEP-05 を充足 |
| L1-REQUIREMENTS.md §3.9 NFR-03 | API 互換 100% 維持 (11 file × 30+ 箇所) が L1 NFR として確定 |
| PLAN-084 §2.6 | 11 file × 30+ 箇所 adapter 表の正本。本文書 §3 の根拠 |
| D-API-EXTENDED-draft-v0.1 | 前段 D-API 拡張 (PLAN-070 起源)。本文書は 6 db 分離専用差分 |

### 1.4 実装対象 file と _write_connection signature

`cli/lib/helix_db._write_connection` の現行 signature (2026-05-17 確認):

```python
@contextmanager
def _write_connection(db_path: str | Path | None, ensure_schema: bool = True):
    """db_path=None の場合、_resolve_db_path で HELIX_DB 環境変数 or デフォルトパスへ解決する。"""
    target_path = _resolve_db_path(db_path)
    _prepare_db_path(target_path)
    with file_lock(HELIX_DB_LOCK_NAME):
        conn = _connect(target_path)
        try:
            if ensure_schema:
                _ensure_schema(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
```

11 file が `helix_db._write_connection(None)` と呼ぶことで、現在は単一 helix.db へ write している。
compatibility_adapter.py はこの呼び出し慣行を破壊せず 6 db へ routing する。

---

## §2 compatibility_adapter.py の API 設計

### 2.6 `_DualWriteConnection` 同期 method 仕様（byte-level 追加）

`D-API-SEP-phase4b-addendum` の §A を統合する。

実装は次の 2 箇所で分離実装される:
- `cli/lib/dual_write_connection.py`（`_DualWriteConnection` 本体）
- `cli/lib/compatibility_adapter.py`（`write_connection` routing 経路および呼び出し元切替）

```python
class _DualWriteConnection:
    """legacy + new db を atomic 2 phase commit で扱う synchronized wrapper."""

    def __init__(self, legacy_conn: sqlite3.Connection, new_conn: sqlite3.Connection): ...
    def execute(self, sql: str, params=()) -> sqlite3.Cursor: ...
    def executemany(self, sql: str, params_list) -> sqlite3.Cursor: ...

    def commit(self) -> None:
        """Commit legacy -> new; new-only failure is warning, legacy failure raises."""

    def rollback(self) -> None:
        """Attempt rollback on both DBs even if the first rollback fails."""

    def close(self) -> None: ...

    @property
    def lastrowid(self) -> int | None:
        """Return the legacy connection lastrowid during the dual-write window."""
```

error policy（byte-level）:

- legacy write 失敗（`execute`/`executemany`）: `critical` → `raise`
- new write 失敗: `warn` log のみ、legacy 成功を優先
- commit 失敗（legacy）: 両 DB rollback 試行後 `critical` raise
- commit 失敗（new only）: `rollback` 後 `warn` log のみ
- lock / `SQLITE_BUSY` 超過（retry 上限）: `critical` raise

本節は `docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md`（status: merged）へ双方向 trace 参照している。

### 2.1 旧 `_write_connection(None)` 互換 API

```python
# cli/lib/compatibility_adapter.py
from contextlib import contextmanager
from pathlib import Path
from sqlite3 import Connection
from typing import Iterator, Optional
import inspect
import logging
import os

logger = logging.getLogger(__name__)

@contextmanager
def write_connection(db_path: Optional[str] = None) -> Iterator[Connection]:
    """旧 helix_db._write_connection(None) の API 互換版。

    db_path が指定された場合 (None 以外): 旧来の helix_db._write_connection(db_path) へ委譲。
    db_path=None の場合: caller の context (file path / function name / table name) から
    6 db 経路を自動 routing し、HELIX_DB_CUTOVER 環境変数に応じて
    - 旧 helix.db + 新 6 db 両方 (dual-write 期間中、HELIX_DB_CUTOVER=0)
    - **新 6 db のみ** (cutover 後、HELIX_DB_CUTOVER=1。旧 helix.db への write は停止)
    への write を行う virtual connection を返す。

    呼び出し側の import 切替のみで動作するため、内部ロジック変更は不要。
    """
    if db_path is not None:
        # 既存 explicit db_path 指定は旧来動作を維持
        from . import helix_db
        with helix_db._write_connection(db_path) as conn:
            yield conn
        return

    # db_path=None の場合: caller context から routing 先を決定
    caller_frame = inspect.stack()[2]  # write_connection の 2 フレーム上が実際の caller
    caller_file = caller_frame.filename
    caller_func = caller_frame.function
    target_db = _route_to_db(caller_file, caller_func)

    cutover = os.environ.get("HELIX_DB_CUTOVER", "0") == "1"
    from . import helix_db

    if cutover:
        # cutover 後: 6 db のみへ write
        db_path_6 = _db_path_for(target_db)
        with _new_db_connection(db_path_6) as conn:
            yield conn
    else:
        # dual-write 期間: 旧 helix.db + 新 6 db 両方へ write
        with helix_db._write_connection(None) as legacy_conn:
            db_path_6 = _db_path_for(target_db)
            with _new_db_connection(db_path_6) as new_conn:
                yield _DualWriteConnection(legacy_conn, new_conn, target_db)
```

### 2.2 6 db routing 判定

caller の context (file path + table 名) から canonical db を静的 mapping で決定する。

**routing 優先順位**: `caller_file` による file 直接マッピング → fallback 時のみ table 名 prefix で判定

```python
# cli/lib/compatibility_adapter.py
_FILE_TO_DB: dict[str, str] = {
    # orchestration.db 経路
    "agent_slots.py":        "orchestration",
    "harness_monitor.py":    "orchestration",
    # scrum.db 経路
    "scrum_local.py":        "scrum",
    "reverse_local.py":      "scrum",
    # backend.db 経路 (http_api/routes)
    "audit.py":              "backend",
    "push_pr.py":            "backend",
    "hooks.py":              "backend",
    "telemetry.py":          "backend",
    # backend.db 経路 (top-level CLI)
    "helix-pr":              "backend",
    "helix-push":            "backend",
    # orchestration.db 経路 (top-level CLI)
    "helix-agent":           "orchestration",
}

_TABLE_PREFIX_TO_DB: dict[str, str] = {
    "phase_":        "orchestration",
    "gate_":         "orchestration",
    "sprint_":       "orchestration",
    "agent_":        "orchestration",
    "artifact_":     "vmodel",
    "test_design_":  "vmodel",
    "hypothesis_":   "scrum",
    "poc_":          "scrum",
    "scrum_loop_":   "scrum",
    "reverse_local_": "scrum",
    "plan_":         "plan",
    "task_":         "plan",
    "wbs_":          "plan",
    "automation_":   "backend",
    "audit_":        "backend",
    "session_":      "backend",
}

def _route_to_db(caller_file: str, caller_func: str) -> str:
    """caller の file path から canonical db を決定する。
    file 直接マッピングが優先。未知の caller は HELIX_DB_DISCOVERY=1 (discovery mode)
    でのみ orchestration.db に fallback + WARN、production では fail-close する。
    (tl-advisor L3 review P1 #3 反映: entity ownership 破壊を防ぐ)
    """
    basename = Path(caller_file).name
    if basename in _FILE_TO_DB:
        return _FILE_TO_DB[basename]

    # fallback: table 名 prefix を caller_func から推定 (table INSERT 系関数名に限定)
    for prefix, db_name in _TABLE_PREFIX_TO_DB.items():
        if prefix in caller_func.lower():
            return db_name

    # production = fail-close、discovery mode のみ orchestration.db fallback + WARN
    if os.environ.get("HELIX_DB_DISCOVERY") == "1":
        logger.warning(
            "compatibility_adapter (discovery mode): unknown caller '%s' in '%s', "
            "falling back to orchestration.db. "
            "Add to _FILE_TO_DB mapping before production deployment.",
            caller_func, caller_file
        )
        return "orchestration"
    raise RuntimeError(
        f"compatibility_adapter: unknown caller '{caller_func}' in '{caller_file}'. "
        f"production fail-close (entity ownership 違反防止)。"
        f"_FILE_TO_DB mapping に追加するか、HELIX_DB_DISCOVERY=1 で discovery mode を有効化してください。"
    )
```

### 2.3 dual-write 期間中の I/O 経路

```python
# cli/lib/compatibility_adapter.py

class _DualWriteConnection:
    """dual-write 期間中の virtual connection。
    legacy_conn (旧 helix.db) への write を primary とし、
    new_conn (新 6 db) への write を secondary とする。
    execute() の結果は legacy_conn の lastrowid / rowcount を返す (API 互換保証)。
    """

    def __init__(self, legacy_conn: Connection, new_conn: Connection, target_db: str):
        self._legacy = legacy_conn
        self._new = new_conn
        self._target_db = target_db

    def execute(self, sql: str, parameters=()) -> "sqlite3.Cursor":
        cursor = self._legacy.execute(sql, parameters)
        try:
            self._new.execute(sql, parameters)
        except Exception as e:
            logger.warning(
                "compatibility_adapter: dual-write to %s.db failed: %s "
                "(legacy write succeeded, continuing)",
                self._target_db, e
            )
        return cursor  # legacy cursor を返すことで API 互換を維持

    def executemany(self, sql: str, parameters) -> "sqlite3.Cursor":
        cursor = self._legacy.executemany(sql, parameters)
        try:
            self._new.executemany(sql, parameters)
        except Exception as e:
            logger.warning(
                "compatibility_adapter: dual-write (executemany) to %s.db failed: %s",
                self._target_db, e
            )
        return cursor
```

**dual-write の切替制御**:

| 状態 | 環境変数 | I/O 経路 |
|---|---|---|
| migration gate 1-4 (dual-write 期間) | `HELIX_DB_CUTOVER` 未設定 or `"0"` | 旧 helix.db **+** 新 6 db 両方に write |
| migration gate 5 (cutover) 後 | `HELIX_DB_CUTOVER=1` | 6 db のみへ write (旧 helix.db への write 停止) |

### 2.4 transaction 境界

SQLite ATTACH 下では cross-db transaction は単一 db に閉じる。以下の原則を adapter が保証する:

- **同一 caller の write 群 = 同一 db への write のみ → atomic**:
  同一 caller file の _FILE_TO_DB マッピングが 1 db を返すため、caller の一連の `with write_connection()` ブロックは常に同一 6 db へ write される。cross-db atomic transaction は発生しない
- **cross-db write が必要な場合**: separate transaction で順次実行 (rollback 不可)。application logic で整合性を担保する。本設計では 11 file がそれぞれ単一 db に routing されるため cross-db write は発生しない設計
- **dual-write 期間の _DualWriteConnection**: legacy_conn (primary) が commit / rollback されると同期的に new_conn も commit / rollback する。new_conn の失敗は WARN 止まりで legacy の整合性を優先 (dual-write 期間の設計上の許容)

### 2.5 error handling

| エラー発生箇所 | dual-write 期間 (gate 1-4) | cutover 後 (gate 5 以降) |
|---|---|---|
| 旧 helix.db への write 失敗 | **critical** (例外を raise、呼び出し側に伝播) | N/A (旧 db への write なし) |
| 新 6 db への write 失敗 | **WARN** (log のみ、処理継続) | **critical** (例外を raise) |
| routing 先不明 (unknown caller) | **production default: `RuntimeError` fail-close** (entity ownership 違反防止) / `HELIX_DB_DISCOVERY=1` 環境変数で discovery mode 有効化時のみ WARN + orchestration.db fallback | 同左 (tl-advisor L3 review Round 2 P1 #2 反映、§2.2 と整合) |

---

## §3 11 file 別 adapter 動作

各 file の `_write_connection(None)` 呼び出しが何 db に routing されるか、callsite 数と adapter test 観点を契約として確定する。

| # | file | callsite 数 | routing 先 db | adapter test 観点 |
|---|---|---|---|---|
| 1 | `cli/lib/agent_slots.py` | 5 | orchestration.db | `fire_slot` / `release_slot` / `update_slot_session` / `check_duplicate_slot` / `stats` の全 path で agent_slots table CRUD が orchestration.db に到達すること |
| 2 | `cli/lib/harness_monitor.py` | 4 | orchestration.db | `harness_monitor_events` / `monitor_runs` table の INSERT / UPDATE が orchestration.db に到達すること |
| 3 | `cli/lib/scrum_local.py` | 6 | scrum.db | `hypothesis` / `poc` / `verify` / `decide` / `scrum_loop_local` の INSERT / UPDATE が scrum.db に到達すること |
| 4 | `cli/lib/reverse_local.py` | 5 | scrum.db | `reverse_local_loops` table の CRUD が scrum.db に到達すること |
| 5 | `cli/lib/http_api/routes/audit.py` | 1 | backend.db | `audit_log` INSERT が backend.db に到達すること |
| 6 | `cli/lib/http_api/routes/push_pr.py` | 3 | backend.db | `automation_run` INSERT / UPDATE (3 path: create / update_status / complete) が backend.db に到達すること |
| 7 | `cli/lib/http_api/routes/hooks.py` | 1 | backend.db | hook callback 由来の `audit_log` INSERT が backend.db に到達すること |
| 8 | `cli/lib/http_api/routes/telemetry.py` | 1 | backend.db | `session_telemetry` UPSERT が backend.db に到達すること |
| 9 | `cli/helix-pr` (top-level CLI) | 2 | backend.db | PR 作成 / 更新時の `automation_run` INSERT / UPDATE が backend.db に到達すること (smoke test 必須) |
| 10 | `cli/helix-push` (top-level CLI) | 2 | backend.db | push event の `automation_run` INSERT / UPDATE が backend.db に到達すること (smoke test 必須) |
| 11 | `cli/helix-agent` (top-level CLI、embed Python) | 1 | orchestration.db | `agent_slots` SELECT (read-only path) が orchestration.db に到達すること (smoke test 必須) |

**Phase 4.A の adapter 実装方針**:

- 各 file は `from . import helix_db` の代わりに `from . import compatibility_adapter as helix_db` と import を切り替えるのみで動作する
- `write_connection` が `_write_connection` と同名でない場合: `helix_db._write_connection = compatibility_adapter.write_connection` のモンキーパッチで対応可能 (Phase 4.A の Codex se が実装判断)
- 内部ロジック (SQL 文 / parameter / commit タイミング) は一切変更しない

---

## §4 cross-db read helper

### 4.1 projection_state 経由の cross-db read API

```python
# cli/lib/compatibility_adapter.py

def read_cross_db_projection(projector_id: str, db_name: str) -> Optional[dict]:
    """他 db の projection_state snapshot を read する。

    Args:
        projector_id: 'phase_projector' / 'gate_projector' / 'agent_slot_projector'
        db_name: 取得先 db 名 ('orchestration' / 'vmodel' / 'scrum')

    Returns:
        snapshot dict (projection_state.snapshot の JSON を parse したもの)。
        projector_id が未知、または snapshot が None の場合は None を返す。

    制約:
        - read のみ。write は一切行わない。
        - ATTACH は使用しない。db_name で指定された db file に直接 connect する。
        - lag 監視: last_processed_event_id と event_envelope の最新 event_id を比較し、
          lag > 100 event の場合は WARN log を出力する。
    """
    db_path = _db_path_for(db_name)
    if not db_path.exists():
        logger.warning("read_cross_db_projection: db file not found: %s", db_path)
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT last_processed_event_id, snapshot, updated_at "
            "FROM projection_state WHERE projector_id = ? AND db_name = ?",
            (projector_id, db_name)
        ).fetchone()
        if row is None:
            return None

        # lag 監視 (100 event 超過で WARN)
        _check_projector_lag(conn, db_name, row["last_processed_event_id"], projector_id)

        snapshot_raw = row["snapshot"]
        if snapshot_raw is None:
            return None
        return json.loads(snapshot_raw)
    finally:
        conn.close()
```

### 4.2 同期許可 3 projector からの read 例

ADR-018 §Decision.3 で確定した同期許可 3 件を caller から read する標準パターン:

```python
# 例: phase 状態を orchestration.db の projection から取得
phase_snapshot = read_cross_db_projection("phase_projector", "orchestration")
if phase_snapshot:
    current_phase = phase_snapshot.get("current_phase")

# 例: gate 通過状態を確認
gate_snapshot = read_cross_db_projection("gate_projector", "orchestration")
if gate_snapshot:
    g4_status = gate_snapshot.get("gates", {}).get("G4", {}).get("status")

# 例: agent slot の空き確認
slot_snapshot = read_cross_db_projection("agent_slot_projector", "orchestration")
if slot_snapshot:
    active_count = slot_snapshot.get("active_slot_count", 0)
```

### 4.3 stale data 許容と lag warning

```python
def _check_projector_lag(
    conn: Connection, db_name: str, last_event_id: str, projector_id: str
) -> int:
    """projector lag を計算し、警告境界を超えた場合に WARN を出す。
    lag event 数を返す。"""
    row = conn.execute(
        "SELECT COUNT(*) as lag FROM event_envelope "
        "WHERE db_name = ? AND event_id > ?",
        (db_name, last_event_id)
    ).fetchone()
    lag = row["lag"] if row else 0

    if lag >= 1000:
        logger.error(
            "projector lag CRITICAL: projector=%s db=%s lag=%d events "
            "(>= 1000 threshold, gate fail-close active in Phase 4.B+)",
            projector_id, db_name, lag
        )
    elif lag >= 100:
        logger.warning(
            "projector lag WARNING: projector=%s db=%s lag=%d events",
            projector_id, db_name, lag
        )
    return lag
```

**HTTP API での lag warning ヘッダー付与**:

- lag > 100 event: response header `X-Projection-Lag: <n>` を付与 (HTTP API route 層で実装、Phase 4.B)
- CLI での lag WARN: logger.warning のみ (上記 `_check_projector_lag` の WARN log)

### 4.4 Reverse 機能の例外

ADR-018 §Decision.1 Reverse 例外 (G-07 境界) の adapter レベルでの実装方針:

- Reverse 機能 (R0-R4 + RGC) は `read_cross_db_projection` の read のみ許可
- `write_connection` を通じた event log への write は Reverse caller では発生しない (Reverse は artifact strand を逆方向に辿る操作)
- `cli/lib/reverse_local.py` が routing される先は `scrum.db` (§3 #4 参照)。scrum_local_loops table への write が Reverse 機能の唯一の 6 db write であり、event log への write とは別物

---

## §5 ATTACH 制限 + CI gate

### 5.1 ATTACH allowlist (D-DB-SEP §5.2 と同期)

ATTACH DATABASE の使用が許可されるコンテキストは D-DB-SEP-draft §5.2 と完全に同期する:

| 許可コンテキスト | ファイルパス | 用途 |
|---|---|---|
| migration script | `cli/lib/migrations/*.py` | v30 → v31 の schema 変更・初期化 |
| projector 内部 | `cli/lib/projectors/*.py` | cross-db projection_state の read |

**禁止コンテキスト**:

| 禁止コンテキスト | ファイルパス |
|---|---|
| アプリ層 CLI | `cli/helix-*` |
| HTTP API routes | `cli/lib/http_api/**/*.py` |
| 通常の lib helper | `cli/lib/agent_slots.py` / `cli/lib/harness_monitor.py` 等 |
| compatibility_adapter.py 自身 | ATTACH を使わず db file に直接 connect することで cross-db read を実現 |

**compatibility_adapter.py の cross-db read は ATTACH を使わない公認 helper 経路**:
`read_cross_db_projection` は projection_state を read する際に ATTACH ではなく
`sqlite3.connect(db_path)` で直接 db file に接続する。これは ATTACH allowlist 制約を
bypass するのではなく、**allowlist と無関係な別経路で cross-db read を実現** する設計。
allowlist 外の caller (app 層 lib helper 等) からも安全に projection_state を read 可能
(tl-advisor L3 review P3 反映、「回避」表現を「公認 helper 経路」に明確化)。

### 5.2 ATTACH 禁止 CI gate

Phase 4.A の Sprint Exit 条件として CI で以下の grep を実行し、0 件であることを確認する:

```bash
#!/bin/bash
# scripts/check_attach_boundary.sh (Phase 4.A で配置)
# ATTACH DATABASE の禁止コンテキスト使用チェック

echo "=== ATTACH 禁止コンテキストチェック ==="

# アプリ層 CLI での ATTACH チェック
RESULT_CLI=$(grep -rn "ATTACH DATABASE" cli/helix-* 2>/dev/null | grep -v "^Binary")
# HTTP API routes での ATTACH チェック
RESULT_HTTP=$(grep -rn "ATTACH DATABASE" cli/lib/http_api/ 2>/dev/null)
# lib helper (migrations / projectors 除外) での ATTACH チェック
RESULT_LIB=$(grep -rn "ATTACH DATABASE" cli/lib/ \
  --exclude-dir=migrations \
  --exclude-dir=projectors \
  2>/dev/null)

FAIL=0
if [ -n "$RESULT_CLI" ]; then
    echo "FAIL: ATTACH in cli/helix-*:"
    echo "$RESULT_CLI"
    FAIL=1
fi
if [ -n "$RESULT_HTTP" ]; then
    echo "FAIL: ATTACH in cli/lib/http_api/:"
    echo "$RESULT_HTTP"
    FAIL=1
fi
if [ -n "$RESULT_LIB" ]; then
    echo "FAIL: ATTACH in cli/lib/ (non-migrations/projectors):"
    echo "$RESULT_LIB"
    FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
    echo "PASS: ATTACH 禁止コンテキスト 0 件"
fi
exit $FAIL
```

期待: 全て 0 件 (allowlist 外で ATTACH 検出 → CI fail)。
配置場所: `.github/workflows/` の lint job または `helix push` gate の pre-check として実装 (Phase 4.A carry)。

### 5.3 lint integration (carry)

ruff / pylint での custom rule (ATTACH 禁止) 追加を Phase 4.A carry として検討する。
静的 AST 解析による検出は grep ベース CI gate と相補的。実装コストが高い場合は grep gate のみで代替可。

---

## §6 cli/libexec/helix-session-start 対象外根拠

### 6.1 callsite の存在確認

`cli/libexec/helix-session-start:155` に `helix_db._write_connection(db_path)` の callsite が 1 件存在する。
ここで渡される引数は `db_path` (None ではない明示的なパス) である。

### 6.2 adapter 対象外の根拠

本 §6.2 は tl-advisor Round 2 carry (D-DB-SEP-draft §7 carry #4 "cli/libexec/helix-session-start を
adapter 対象外にする根拠明記") を本文書で履行する。

| 根拠 | 詳細 |
|---|---|
| **internal helper** | `cli/libexec/` 配下は top-level CLI (`cli/helix-*`) から呼ばれる internal helper。通常の CLI 呼び出しとは異なる起動 path であり、PLAN-084 §2.6 の adapter 対象 "top-level CLI 3 件 (helix-pr / helix-push / helix-agent)" に含まれない |
| **明示 db_path 渡し** | `_write_connection(db_path)` と呼んでおり `db_path=None` ではない。adapter の routing 対象は `_write_connection(None)` 呼び出しのみ。明示的な db_path 指定は routing 不要 |
| **低頻度起動** | session 起動時のみ呼ばれる。adapter routing が必要な高頻度 business logic (agent_slots / http_api/routes 等) とは性格が異なる |
| **既存動作の維持** | adapter 適用外とすることで helix-session-start の動作を変更しない。Phase 4.A の adapter test は通常 path (11 file) のみカバー |

### 6.3 Phase 4.A 着手時の確認

Phase 4.A 着手時に以下を smoke test で確認する (§7 carry #7 参照):

- `cli/libexec/helix-session-start` が明示 `db_path` を渡して `_write_connection` を呼ぶ動作を確認
- adapter 適用後も helix-session-start が正常動作することを確認 (adapter を経由しない path)
- `_write_connection(None)` が 0 件であることを grep で確認:
  ```bash
  grep -n "_write_connection(None)" cli/libexec/helix-session-start
  # 期待: 0 件
  ```

### 6.4 tl-advisor Round 2 carry 反映済

本 §6 全体が D-DB-SEP-draft §7 carry #4 の対応として起票されている。本 §6.2 の根拠明記を
もって carry #4 の L3 設計レベル履行完了とする。Phase 4.A の Codex se が smoke test 実施後、
§7 carry #7 を完了マークする。

---

## §7 carry to Phase 4

Phase 4 実装で確定・実施する事項:

| # | carry 項目 | 確定 phase | 担当 |
|---|---|---|---|
| 1 | `compatibility_adapter.py` 本実装 (`write_connection` / `_DualWriteConnection` / `_route_to_db` / `_db_path_for`) | Phase 4.A | Codex se |
| 2 | 6 db routing logic の `_FILE_TO_DB` mapping 完全版確定 (Phase 4.A 着手時に `grep -rln "_write_connection" cli/` 再実行で漏れ確認) | Phase 4.A | Codex se |
| 3 | `read_cross_db_projection` 実装 + `_check_projector_lag` 実装 | Phase 4.A | Codex se |
| 4 | adapter unit test: 11 file × 30+ callsite path カバー (`cli/lib/tests/test_compatibility_adapter.py`) | Phase 4.A | Codex qa |
| 5 | top-level CLI 3 件 smoke test: `helix-pr` / `helix-push` / `helix-agent list` が adapter 経由で正常動作 (`cli/tests/db_separation_smoke.bats`) | Phase 4.A | Codex qa |
| 6 | ATTACH 禁止 grep CI gate 実装 (`scripts/check_attach_boundary.sh` + CI job 組み込み) | Phase 4.A | Codex se |
| 7 | `cli/libexec/helix-session-start` adapter 対象外確認 smoke test (grep で `_write_connection(None)` 0 件 確認) | Phase 4.A | Codex qa |
| 8 | dual-write 期間中の error log 監視 (旧 db 失敗 = critical raise / 新 db 失敗 = WARN log) が `test_compatibility_adapter.py` でカバー | Phase 4.B | Codex se |
| 9 | adapter 経由の transaction 制限 (cross-db rollback 不可) を runbook に明記 (caller side への周知) | Phase 4.A | PM (runbook) |
| 10 | `HELIX_DB_CUTOVER` 環境変数の docs/runbook 起票 (cutover 手順 + rollback 手順) | Phase 4.C | PM |
| 11 | HTTP API での `X-Projection-Lag: <n>` response header 付与 (lag > 100 event 時) | Phase 4.B | Codex se |
| 12 | lint integration (ruff / pylint custom rule: ATTACH 禁止) 実装可否判断 | Phase 4.A | Codex se |
| 13 | adapter test の受入条件: 「ラッパー / monkeypatch 適用後も `inspect.stack()[N]` の caller 判定がずれない」を `test_compatibility_adapter.py` に明示 (tl-advisor L3 review P3 反映、unit test 設計 U-ADAPTER-014/015 でカバー済) | Phase 4.A | Codex qa |
| 14 | `inspect.stack()[2]` frame index 実測確定 (Python 実行環境での frame depth 検証、production 適用前に PM 承認、tl-advisor L3 review carry) | Phase 4.A | Codex se |

**carry 優先度**:

- **Phase 4.A 必須**: #1 (adapter 本実装) / #2 (routing mapping 確定) / #3 (read helper) / #4 (unit test) / #5 (smoke test) / #6 (CI gate) / #7 (session-start 確認) / #9 (runbook)
- **Phase 4.B 必須**: #8 (error log 監視 test) / #11 (lag header)
- **Phase 4.C 必須**: #10 (cutover runbook)
- **判断 carry**: #12 (lint integration)

---

## §8 V-model trace

設計⇔テスト対応 (HELIX_CORE.md §V-model 4 artifact 双方向 trace / PLAN-075 準拠):

| artifact | 本文書との関係 |
|---|---|
| **① 設計** (本文書) | D-API-SEP-draft-v0.1。L3 詳細設計 / 結合テスト設計レイヤー (L3 機能設計 → 単体テスト設計も含む) |
| **② 実装コード** | `cli/lib/compatibility_adapter.py` (Phase 4.A 新規起票) |
| **③ テスト設計** | `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` §2 (U-ADAPTER-001〜015、Phase 3.4 起票済、commit ff04129) + `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` §6 (I-SMOKE、top-level CLI smoke) |
| **④ テストコード** | `cli/lib/tests/test_compatibility_adapter.py` (Phase 4.A) + `cli/tests/db_separation_smoke.bats` (Phase 4.A) |

**双方向 trace**:

- **本 doc → ③ テスト設計**: `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` §2 (U-ADAPTER-001〜015) + `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` §6 (I-SMOKE-001〜006) (Phase 3.4 起票済、commit ff04129)
- **本 doc → ② 実装コード**: `cli/lib/dual_write_connection.py` (`_DualWriteConnection` 本体) + `cli/lib/compatibility_adapter.py` (write_connection routing)
- **③ テスト設計 → 本 doc**: PLAN-084-unit-test-design.md frontmatter `related_designs` に「D-API-SEP-draft-v0.1」明示済
- **④ テストコード → ③ テスト設計**: テスト docstring に「DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-XXX / PLAN-084-integration-test-design.md I-SMOKE-XXX」を明示 (Phase 4.A)
- **本 doc ⇔ D-DB-SEP-draft**: 本 doc §5 (ATTACH allowlist) は D-DB-SEP §5.2 と同期。scrum.db routing は D-DB-SEP §2.3 の entity ownership に準拠。backend.db routing は D-DB-SEP §2.5 に準拠

---

## §9 References

| 文書 | 参照箇所 |
|---|---|
| `docs/adr/ADR-018-db-separation-and-event-sourcing.md` §Decision.5 | 本文書全体の根拠。compatibility adapter の責務・dual-write 制御・API 互換 100% 維持要件 |
| `docs/adr/ADR-018-db-separation-and-event-sourcing.md` §Decision.1 | ATTACH 禁止規約の根拠。本文書 §5 の根拠 |
| `docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft-v0.1` §2-6 | sibling doc。本文書と双方向 trace。schema 正本、entity ownership 表、migration gate 順序 |
| `docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft-v0.1` | 前段 D-API 拡張 (PLAN-070 起源)。本文書は 6 db 分離専用差分 |
| `docs/plans/PLAN-084-helix-db-separation-and-event-sourcing.md` §2.6 | 11 file × 30+ 箇所 adapter 表の正本。本文書 §3 の根拠 |
| `docs/v2/L1-REQUIREMENTS.md` §3.9 FR-DB-SEP-06 | migration gate 6 段階の受入条件。本文書全体の L1 接続点 |
| `docs/v2/L1-REQUIREMENTS.md` §3.9 NFR-03 | API 互換 100% 維持 (11 file × 30+ 箇所) の L1 NFR |
| `cli/lib/helix_db.py` `_write_connection` (L1052) | adapter の互換 target。現行 signature を §1.4 で確認済 |
| `cli/lib/agent_slots.py` | lib callsite 5 件の使用 pattern 確認済。`fire_slot` / `release_slot` が `_write_connection(None)` を使用 |
| `D-CONTRACT-EVENT-draft-v0.1` (Phase 3.3 起票予定) | sibling doc。event envelope Python class 正本 (本文書は schema のみ参照) |
