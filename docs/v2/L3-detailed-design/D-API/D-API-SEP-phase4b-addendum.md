---
id: D-API-SEP-phase4b-addendum
plan: PLAN-084
layer: L3
status: merged
created: 2026-05-18
addendum_for: D-API-SEP-draft.md
triggered_by: tl-advisor verdict 2026-05-18 (5 P1 + 3 P2 指摘)
---

# PLAN-084 Phase 4.B: dual-write + projector + mismatch freeze addendum

本 addendum は `D-API-SEP-draft.md`（PLAN-084、Phase 4.B）と
`D-CONTRACT-EVENT-draft.md` の tl-advisor 指摘を受け、実装可否を確定する
補助 frozen contract である。  
対象は既存 doc の本文（`D-API-SEP-draft.md`/`D-CONTRACT-EVENT-draft.md`）ではなく、
本ファイルに限定して byte-level を凍結する。

本 addendum の内容は `D-API-SEP-draft.md §2.6` と `D-CONTRACT-EVENT-draft.md §4` に  
`2026-05-18` 付で統合済みのため、参照用として残すのみとする。

## A. `_DualWriteConnection` 同期 method 仕様（P1）

`cli/lib/compatibility_adapter.py`（実装場所）は別 PLAN で carry し、本 addendum は API 契約を確定する。

### A-1. class / method signature

```python
class _DualWriteConnection:
    """legacy + new db を atomic で 2 phase commit する synchronized wrapper.

    Phase 4.B.4 で本実装、Phase 4.B.8 で mismatch detector と統合。
    """
    def __init__(self, legacy_conn: sqlite3.Connection, new_conn: sqlite3.Connection): ...
    def execute(self, sql: str, params=()) -> sqlite3.Cursor: ...
    def executemany(self, sql: str, params_list) -> sqlite3.Cursor: ...
    def commit(self) -> None:
        """legacy → new の順で commit。new 失敗時は WARN のみ、legacy 失敗は raise。"""
    def rollback(self) -> None:
        """両 db rollback。例外時も rollback 試行は両 db に対して行う (best-effort)。"""
    def close(self) -> None: ...
    @property
    def lastrowid(self) -> int | None:
        """legacy_conn.lastrowid を返す (new_conn.lastrowid は dual-write 期間中は参照しない)"""
```

### A-2. error policy

- legacy write 失敗 (`execute`/`executemany` 内での `sqlite3` 例外)
  - severity: `critical`
  - action: `raise`
- new write 失敗
  - severity: `warn`
  - action: `warn` log のみ、`legacy` 成功として扱う（例外を raise しない）
- `commit` 失敗（legacy）
  - action: legacy と new の両方で `rollback()` を試行し、`critical` raise
- `commit` 失敗（new only）
  - action: new に対して `rollback()` → `warn` log のみ
- lock / `SQLITE_BUSY`（いずれかの commit / rollback / execute）
  - retry 上限: 5 回
  - backoff: 100ms
  - 超過: `critical` raise

## B. projector 3 件の signature / schema / event_type / table（P1）

### B-1. 共通 Protocol

```python
class Projector(Protocol):
    projector_id: str
    target_db: str   # "orchestration" | "vmodel" | "scrum"
    interesting_event_types: tuple[str, ...]
    
    def apply(self, envelope: EventEnvelope, current_snapshot: dict | None) -> dict:
        """event を適用して新 snapshot を返す。snapshot は JSON serializable dict。"""
    
    def initial_snapshot(self) -> dict:
        """新規 projector 起動時の初期 snapshot (空 state)。"""
```

### B-2. 個別 projector contract

| projector_id | 対象 db | 対象 event_type | snapshot JSON schema | record table |
|---|---|---|---|---|
| `phase_state` | orchestration | `phase.transitioned`, `phase.entered`, `phase.exited` | `{"current_phase": "L4", "previous_phase": "L3", "transitioned_at": "..."}` | `projection_state` (`orchestration.db`) |
| `artifact_chain` | vmodel | `artifact.created`, `artifact.linked` | `{"artifacts": [{"id": "...", "type": "...", "parent_id": "..."}]}` | `projection_state` (`vmodel.db`) |
| `hypothesis_state` | scrum | `hypothesis.added`, `hypothesis.confirmed`, `hypothesis.rejected` | `{"hypotheses": [{"id": "...", "status": "confirmed", "decided_at": "..."}]}` | `projection_state` (`scrum.db`) |

- projector 実装ファイルは `cli/lib/projectors/<projector_id>.py`
- registry 登録は `cli/lib/projectors/__init__.py` を経由する
- `initial_snapshot()` は空 state を返す
- `apply()` は引数 `current_snapshot` が `None` の場合に `initial_snapshot()` を先適用する
- `apply()` の戻り値は JSON serializable の `dict` を必ず返す

## C. mismatch detector contract（P1）

```python
@dataclass(frozen=True)
class MismatchResult:
    detected: bool
    table_name: str
    legacy_row_count: int
    new_row_count: int
    mismatch_keys: list[str]   # 不一致 row の primary key
    detected_at: str           # ISO8601 UTC
    severity: str              # "warn" | "critical"

def check_dual_write_mismatch(
    legacy_conn: sqlite3.Connection,
    new_conn: sqlite3.Connection,
    table_name: str,
    *,
    sample_size: int = 1000,
) -> MismatchResult:
    """legacy と new の row 一致確認 (sample_size 件まで)。"""
```

### C-1. 補足仕様

- sample 取得上限: `sample_size`（既定 1000）を超える比較をしない
- 停止時の防止: `sample_size` により stop-the-world を回避する
- 保存先: `detector_runs` table（`backend.db`）
- mismatch 記録は `table_name` ごとに legacy/new の行数と差分キーを保持
- `detected=False` 時: `mismatch_keys=[]`, `detected_at` は UTC ISO8601
- `severity` は `warn` または `critical` のみ許容

## D. projector lag 境界値（P2）

```python
LAG_WARN_THRESHOLD = 100  # event count
LAG_CRITICAL_THRESHOLD = 1000

def _check_projector_lag(...) -> int:
    """processed event_id から最新 event_id までの差分を返す。
    
    - lag <= 100: 正常
    - lag > 100 (= 101 以上): WARN log
    - lag > 1000 (= 1001 以上): CRITICAL log + gate fail-close 候補 (Phase 4.B.6 設計)
    """
```

- 判定は「strict greater than」を採用し、`>= 100` は WARN の対象としない
- `lag > 100` の場合のみ WARN
- `lag > 1000` の場合は CRITICAL、Phase 4.B.6 で gate fail-close 候補

## E. `read_cross_db_projection` の unknown projector_id 処理（P2）

```python
_KNOWN_PROJECTORS = frozenset({"phase_state", "artifact_chain", "hypothesis_state"})

def read_cross_db_projection(projector_id: str, db_name: str) -> dict | None:
    if not projector_id:
        raise ValueError("projector_id must not be empty")
    if projector_id not in _KNOWN_PROJECTORS:
        # unknown projector: production fail-close (DISCOVERY mode 不要、明示 contract)
        raise ValueError(
            f"unknown projector_id '{projector_id}'. "
            f"known: {sorted(_KNOWN_PROJECTORS)}"
        )
    _validate_db_name(db_name)
    # db file 不在 → None (skeleton と本実装で同じ動作)
    ...
```

- 空文字 projector_id: `ValueError("projector_id must not be empty")`
- 未知の `projector_id`: `ValueError`（fail-close）
- `db_name` 検証後、DB ファイルがない場合は `None` を返す（実装/スケルトン同一）

## F. correlation context 実装方式（P2）

`D-CONTRACT-EVENT §4` の `threading.local` 記述を本 addendum で `contextvars` へ正規化する。  
実装は Phase 4.B で統一し、対象ファイルは `D-CONTRACT-EVENT` 本体変更なしで carry 扱い。

```python
# 採用
_CORRELATION_CONTEXT: contextvars.ContextVar[CorrelationContext | None] = contextvars.ContextVar(...)
# 非採用
# threading.local / thread local state
```

採用理由:

1. async/await 互換の必要性（将来の web layer 追加時に必須）
2. `contextlib.contextmanager` との親和性
3. `pytest` fixture 間干渉の低減

## 受入条件（この addendum の DoD）

> 統合済み (2026-05-18 merge)。本文は reference として保持。新規作成 DoD は PLAN-084 carry list で完了状態

1. 本 addendum の仕様は `D-API-SEP-draft.md` / `D-CONTRACT-EVENT-draft.md` へ参照統合済み
2. A〜F の 6 項目を以下の全観点で固定:
   - class/function signature
   - return type / param type
   - error policy
   - record destination（必要時）
3. front-matter に以下を含める
   - `id: D-API-SEP-phase4b-addendum`
   - `plan: PLAN-084`
   - `layer: L3`
   - `status: merged`
   - `created: 2026-05-18`
   - `addendum_for: D-API-SEP-draft.md`
   - `triggered_by: tl-advisor verdict 2026-05-18 (5 P1 + 3 P2 指摘)`
4. 末尾に「**Phase 4.B 完遂後の merge tasks**」を追加

## Phase 4.B 完遂後の merge tasks

- `docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md` に対し、A/B/C/D/E を本体実装契約として反映
- `docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` の P2 仕様（F）を `contextvars` ベースで更新
- `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` と
  `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` の該当 case と参照リンクを更新
