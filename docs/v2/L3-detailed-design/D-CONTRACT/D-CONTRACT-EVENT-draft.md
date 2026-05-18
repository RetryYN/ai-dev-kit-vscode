---
doc_id: D-CONTRACT-EVENT-draft-v0.1
plan_id: PLAN-084
sprint: Phase 3 / L3 詳細設計
status: draft
created: 2026-05-17
primary_drive: be
extends: D-CONTRACT-draft-v0.1
related_adrs:
  - ADR-018-db-separation-and-event-sourcing
  - ADR-019-double-helix-naming-principle
related_plans:
  - PLAN-084
sibling_docs:
  - D-DB-SEP-draft-v0.1 (Phase 3.1 起票済、schema 正本)
  - D-API-SEP-draft-v0.1 (Phase 3.2 起票済、adapter API 正本)
---

# PLAN-084 Phase 3: L3 D-CONTRACT EVENT Envelope 詳細設計 v0.1

## §1 目的とスコープ

### 1.1 本文書の位置づけ

本文書は ADR-018 §Decision.1 (event envelope 規約) と D-DB-SEP-draft §3 (event_envelope table schema) を受け、event-sourced 3 db (orchestration / vmodel / scrum) の **event envelope を Python class として確定**する L3 詳細設計書である。

Phase 4.B 実装の正本契約として機能し、Codex se / qa が本文書を参照して `EventEnvelope` dataclass および周辺 API を実装する。

前段文書との関係を以下に整理する:

| 前段文書 | 本文書との関係 |
|---|---|
| ADR-018 §Decision.1 | event envelope 規約の根拠。本文書はこれを Python API レベルに展開する |
| D-DB-SEP-draft §3 | event_envelope table の SQL schema 正本。本文書の §2 dataclass はこの schema と 1:1 対応する |
| D-API-SEP-draft §4 | cross-db read helper との統合点。本文書 §4.4 で参照 |
| L1-REQUIREMENTS.md §3.9 FR-DB-SEP-01/02 | 受入条件の原点。本文書が充足する FR を各節に明示する |
| D-CONTRACT-draft (PLAN-070) | 前段 D-CONTRACT。本文書は EVENT 専用差分として extends する |

### 1.2 スコープ

**In-scope**:

- `EventEnvelope` Python dataclass の定義 (field, type, frozen 設計)
- `generate_event_id()` UUID v7 generator の API signature (実装は Phase 4.A carry)
- `correlation_context` context manager の API signature (実装は Phase 4.B carry)
- payload schema の命名規約と JSON schema 配置方針
- `occurred_at` の format 規約と生成方法
- SQLite シリアライズ用 `to_sqlite_row` / `from_sqlite_row` の責務定義
- carry to Phase 4 の割当表

**Non-goals**:

- 6 db schema 詳細 (D-DB-SEP-draft で扱う)
- compatibility adapter API (D-API-SEP-draft で扱う)
- projector 実装本体 (Phase 4.B で Codex se が担当)
- event_type 全種類の payload schema 列挙 (本文書は規約のみ、event_type 別 schema は Phase 4.B で確定)
- HTTP endpoint 実装 (本 PLAN scope 外。EventEnvelope を HTTP 経由で受け取る endpoint は別 PLAN で扱う、本 doc は Python class の正本のみ確定)
- plan.db の plan_change_log (hybrid 方式につき EventEnvelope 不使用、D-DB-SEP-draft §2.4 参照)
- frontend.db / backend.db (state-store 採用につき EventEnvelope 対象外、ADR-018 §Decision.2 参照)

### 1.3 対象 db の範囲確認

ADR-018 §Decision.2 の 6 軸判定により、EventEnvelope が適用される db は以下の 3 件に限定される。

| db | 採用方式 | EventEnvelope 対象 |
|---|---|---|
| orchestration.db | event-sourced | **対象** |
| vmodel.db | event-sourced | **対象** |
| scrum.db | event-sourced | **対象** |
| plan.db | hybrid (state snapshot + change log) | **対象外** (plan_change_log は独自構造) |
| backend.db | state-store | **対象外** |
| frontend.db | state-store | **対象外** |

### 1.4 前提: aggregate_id の identity 規約

ADR-018 §Decision.1 の確定事項 (tl-advisor Round 2 important #3 反映):

- `event_id`: **global unique** (UUID v7)。全 db を通じて一意
- `aggregate_id`: **db 内 unique** のみ要求。global uniqueness は要求しない
- composite identity: `{db_name, aggregate_type, aggregate_id}` の 3 tuple が aggregate の global identity
- cross-db の event 参照は `correlation_id` で行い、`aggregate_id` の cross-db 比較は行わない

---

## §2 EventEnvelope Python class 設計

### 2.1 dataclass vs Pydantic 選択判断

HELIX 既存コード (`cli/lib/`) は Pydantic を導入しておらず、Python 標準 `dataclasses` と `sqlite3` を主体とした実装スタイルを採用している。

| 比較軸 | dataclass | Pydantic v2 |
|---|---|---|
| 依存追加 | なし (stdlib) | pydantic>=2.0 追加必要 |
| SQLite serialization | tuple 変換が自然 | model_dump → tuple 変換が必要 |
| validation | 手動 validator を追加 | field_validator が豊富 |
| JSON schema | 手動記述 | model_json_schema() 自動生成 |
| frozen / immutability | `frozen=True` で完全 immutable | `model_config = {"frozen": True}` |
| HELIX 既存 pattern 適合 | ◎ (cli/lib/*.py と同じ style) | △ (依存追加・学習コスト) |

**採用決定**: `@dataclass(frozen=True)` を採用する。

理由:
1. HELIX 既存 `cli/lib/` は Pydantic 未導入。依存追加は PLAN-084 スコープ外
2. SQLite tuple I/O が主用途であり、dataclass の `to_sqlite_row` / `from_sqlite_row` パターンが最もシンプル
3. `frozen=True` で event immutability を保証できる (§2.3 参照)

将来 Pydantic 移行は carry (§7 #9)。HELIX 全体の方針確定後に PM が判断する。

### 2.2 EventEnvelope dataclass 定義

D-DB-SEP-draft §3 の event_envelope table (SQL schema) に 1:1 対応する Python class を確定する。

```python
# cli/lib/event_envelope.py
# @helix:index id=event-envelope.EventEnvelope domain=cli/lib
#   summary=event-sourced 3 db 共通 event envelope dataclass (frozen, immutable)
#   対応設計: D-CONTRACT-EVENT-draft-v0.1 §2.2
#   対応 schema: D-DB-SEP-draft-v0.1 §3 event_envelope table

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class EventEnvelope:
    """event-sourced 3 db (orchestration / vmodel / scrum) 共通 event envelope。

    全 field は immutable。event 発行後の変更は audit trail 破綻を招くため禁止。
    DB 制約と対応する Python-level invariant を frozen=True で保証する。

    Contracts (D-CONTRACT-EVENT-draft-v0.1 §2):
      - event_id: global unique (UUID v7)
      - aggregate_id: db 内 unique のみ要求 (global unique 要求しない)
      - db_name: {'orchestration', 'vmodel', 'scrum'} に限定
      - occurred_at: ISO8601 UTC (timezone.utc 必須)
    """

    event_id: str
    """UUID v7 (global unique)。generate_event_id() で生成すること。"""

    aggregate_id: str
    """aggregate の db 内 unique ID。global unique は保証しない。
    global identity は {db_name, aggregate_type, aggregate_id} の composite で決まる。"""

    aggregate_type: str
    """aggregate の種別。例: 'phase' / 'gate' / 'artifact' / 'hypothesis'
    db_name との組み合わせで canonical entity を特定する。"""

    db_name: str
    """event を所有する db の名前。
    許可値: {'orchestration', 'vmodel', 'scrum'}
    state-store (backend / frontend) および hybrid (plan) は対象外。"""

    event_type: str
    """アプリケーション固有のイベント種別。
    命名規約: '<aggregate_type>.<verb>' (過去形動詞)。
    例: 'phase.transitioned' / 'gate.passed' / 'artifact.created'
    event_type ごとに cli/lib/events/schemas/<event_type>.json で JSON schema を管理する。"""

    payload: dict[str, Any]
    """event_type に対応する JSON 形式のペイロード。
    validation は event_type → JSON schema → jsonschema.validate で行う (Phase 4.B carry)。
    本 L3 では dict[str, Any] として受け取り、schema 適合チェックは carry とする。"""

    correlation_id: str
    """cross-db trace に必須。
    orchestration.db の top-level event で発行し、vmodel / scrum の event は継承する。
    format: UUID v7 または短縮 hash 12 文字 (§4.5 で Phase 4.B 確定 carry)。"""

    occurred_at: str
    """event 発生時刻 (ISO8601 UTC)。
    format: datetime.now(timezone.utc).isoformat() の出力形式。
    例: '2026-05-17T18:50:00.123456+00:00'
    DB INSERT 時刻 (record 時刻) とは別物。§6 参照。"""

    def to_sqlite_row(self) -> tuple[str, str, str, str, str, str, str, str]:
        """SQLite event_envelope table への INSERT 用 tuple に変換する (8 列、tl-advisor L3 review Round 2 P1 #3 反映)。

        **serializer は 8 列契約**: domain object と DB schema の対応は以下:
        - 本 serializer の 8 列: event_id / aggregate_id / aggregate_type / db_name / event_type / payload_json / correlation_id / occurred_at
        - DB schema は 9 列 (D-DB-SEP §3.1): 上記 8 列 + `created_at DATETIME DEFAULT CURRENT_TIMESTAMP`
        - **created_at は DB-only**: INSERT 時に SQL の DEFAULT で自動付与、本 serializer / EventEnvelope dataclass は持たない
        - INSERT 文は明示列 8 個を指定 (例: `INSERT INTO event_envelope (event_id, aggregate_id, ...) VALUES (?,?,?,?,?,?,?,?)`)
        - SELECT 文も明示列 8 個を指定 (`SELECT event_id, aggregate_id, ... FROM event_envelope` で created_at を除外)

        Returns:
            (event_id, aggregate_id, aggregate_type, db_name,
             event_type, payload_json, correlation_id, occurred_at)
        """
        return (
            self.event_id,
            self.aggregate_id,
            self.aggregate_type,
            self.db_name,
            self.event_type,
            json.dumps(self.payload, ensure_ascii=False),
            self.correlation_id,
            self.occurred_at,
        )

    @classmethod
    def from_sqlite_row(
        cls,
        row: tuple[str, str, str, str, str, str, str, str],
    ) -> EventEnvelope:
        """SQLite event_envelope table からの SELECT 結果を EventEnvelope に復元する。

        Args:
            row: (event_id, aggregate_id, aggregate_type, db_name,
                  event_type, payload_json, correlation_id, occurred_at)
        """
        (
            event_id,
            aggregate_id,
            aggregate_type,
            db_name,
            event_type,
            payload_json,
            correlation_id,
            occurred_at,
        ) = row
        return cls(
            event_id=event_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            db_name=db_name,
            event_type=event_type,
            payload=json.loads(payload_json),
            correlation_id=correlation_id,
            occurred_at=occurred_at,
        )
```

### 2.3 frozen=True の設計根拠

`frozen=True` は event immutability の Python-level 保証である。

| 理由 | 詳細 |
|---|---|
| audit trail 保護 | event が mutation 可能であれば、過去の phase 遷移 / gate 通過を事後に書き換えられる。frozen で Python layer での誤変更を防止する |
| hash 可能性 | `frozen=True` により `EventEnvelope` が hashable になり、set / dict の key として使用可能になる |
| 意図の明示 | 呼び出し側が「このオブジェクトは変更不可」と明示的に認識できる。append-only event log の設計意図をコード上で表現する |
| SQLite 制約との整合 | D-DB-SEP-draft §3 の event_envelope table は UPDATE を行わない append-only 設計。frozen=True はこの DB 制約を Python layer で鏡写しする |

### 2.4 db_name validation

`db_name` は以下の許可値のみを受け付ける。

```python
_ALLOWED_DB_NAMES = frozenset({"orchestration", "vmodel", "scrum"})
```

validation の実装方針:
- Phase 4.B の実装時に `__post_init__` 相当の validation を追加する (dataclass の frozen=True との両立は `object.__setattr__` を使わず、class method での事前 check で行う)
- 代替: factory function `create_event_envelope(...)` を設け、そこで validation を行い `EventEnvelope` を構築する

```python
def create_event_envelope(
    *,
    aggregate_id: str,
    aggregate_type: str,
    db_name: str,
    event_type: str,
    payload: dict[str, Any],
    correlation_id: str,
) -> EventEnvelope:
    """EventEnvelope の検証付き生成 factory。

    event_id と occurred_at は本関数が生成する (呼び出し側が指定しない)。
    db_name の許可値チェックをここで行う。
    """
    if db_name not in _ALLOWED_DB_NAMES:
        raise ValueError(
            f"db_name must be one of {_ALLOWED_DB_NAMES}, got: {db_name!r}"
        )
    return EventEnvelope(
        event_id=generate_event_id(),
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        db_name=db_name,
        event_type=event_type,
        payload=payload,
        correlation_id=correlation_id,
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )
```

### 2.5 payload validation 方針

`payload` は `dict[str, Any]` として受け取る。event_type ごとの schema 適合チェックは別 validator で行う (carry、Phase 4.B)。

本 L3 doc では以下の規約のみ確定する:

- payload は JSON serializable であること (`json.dumps()` で例外が出ないこと)
- payload は event_type に対応する JSON schema (`cli/lib/events/schemas/<event_type>.json`) に適合すること (Phase 4.B で jsonschema を用いた validator を実装)
- payload の内容が空 dict `{}` であることは許可する (event_type の発生自体が情報を持つ場合)

---

## §3 UUID v7 generator 設計

### 3.1 UUID v7 採用根拠

ADR-018 §Decision.1 は `event_id` を「global unique (UUID v7 推奨)」と凍結している。本節はその根拠と実装方針を確定する。

| 比較軸 | UUID v4 (random) | UUID v7 (time-ordered) |
|---|---|---|
| 時系列 order | 保証なし | 時刻 prefix で時系列 sortable |
| SQLite B-tree index | random insert で page split 多発 | 単調増加 insert で index 効率化 |
| event log ORDER BY | `ORDER BY event_id` が non-deterministic | `ORDER BY event_id` で時系列 order と一致 |
| 衝突確率 | ~2^-61 per event | ~2^-30 per ms (同一 ms 内の乱数部分) |
| Python stdlib | `uuid.uuid4()` で生成可 | 標準では未提供 (Python **3.14** で追加予定、tl-advisor L3 review P2 #4 反映) |
| 可読性 | なし | 先頭 48 bit が timestamp、人間が大まかな時刻を読める |

**採用決定**: UUID v7 を採用する。`event_id` の SQLite ORDER BY による時系列 sort が event log の基本操作であり、UUID v4 の random order は replay / projection の実装を複雑にする。

### 3.2 Python library 選択方針

Python 標準では UUID v7 は **Python 3.14+** で `uuid.uuid7()` として提供される (RFC 9562)。HELIX のローカル環境は Python 3.12.3 のため stdlib 採用不可、外部ライブラリまたは自前実装が必要 (tl-advisor L3 review Round 2 P2 反映、公式 docs https://docs.python.org/3.14/library/uuid.html 参照)。

| 選択肢 | pros | cons |
|---|---|---|
| `uuid7` (PyPI: uuid7-py または uuid7 package) | 軽量、依存最小、MIT ライセンス | 依存追加 (1 件) |
| 自前実装 (`time.time_ns()` + `os.urandom()`) | 依存なし、HELIX 内完結 | RFC 9562 準拠の確認が必要 |
| Python 3.14+ `uuid.uuid7()` | stdlib、追加依存なし | Python バージョン要件引き上げ (3.12.3 では不可) |

**Phase 4.A での確定事項** (carry #1):
1. HELIX の Python バージョン要件を確認する
2. `uuid7` パッケージの MIT ライセンスと依存関係を検証する
3. 自前実装 vs `uuid7` パッケージのどちらを採用するか Phase 4.A Codex se が決定する

### 3.3 generator API signature (L3 確定)

API signature のみ本 L3 で確定する。実装本体は Phase 4.A carry。

```python
# cli/lib/event_envelope.py
# @helix:index id=event-envelope.generate_event_id domain=cli/lib
#   summary=UUID v7 event_id generator (Phase 4.A で実装確定)
#   対応設計: D-CONTRACT-EVENT-draft-v0.1 §3.3

def generate_event_id() -> str:
    """UUID v7 形式の event_id を生成する。

    UUID v7 は時刻 prefix + random suffix で構成され、
    SQLite ORDER BY での時系列 sort と B-tree index 効率を両立する。

    Returns:
        str: UUID v7 形式の文字列 (例: '018f4a1b-9e1c-7000-a000-0123456789ab')
             標準 UUID 文字列形式 (ハイフン区切り 32 hex digits)

    Note:
        Phase 4.A で uuid7 パッケージ採用 or 自前実装を確定する (carry §7 #1)。
        本 L3 は API signature のみ確定し、実装は Phase 4.A Codex se が担当する。

    Raises:
        RuntimeError: UUID v7 生成に失敗した場合 (entropy 不足等)
    """
    raise NotImplementedError("Phase 4.A で実装 (carry)")
```

### 3.4 collision 確率と HELIX scale 評価

UUID v7 の乱数部分は 60-bit (バリアント bit を除く)。同一ミリ秒内の衝突確率は約 2^-30 ≈ 10^-9。

HELIX の想定イベント規模:

| 想定 | 件数 |
|---|---|
| 1 CLI command あたりの event | 1-20 件 |
| 1 日あたりの event (開発中) | ~500 件 |
| 1 年あたりの event | ~180,000 件 |

HELIX scale での衝突確率は事実上 0。UUID v7 の collision 対策として DB に制約を設けることで検出可能 (D-DB-SEP-draft §3.1 の `event_id TEXT NOT NULL UNIQUE` + `(db_name, event_id) composite PRIMARY KEY` が対応、tl-advisor L3 review P2 #5 反映)。

### 3.5 generator 責務の境界

| 責務 | 担当 | 備考 |
|---|---|---|
| event_id 生成 | `generate_event_id()` (本文書) | app 層が呼び出す |
| event_id を EventEnvelope に渡す | `create_event_envelope()` factory | §2.4 参照 |
| event_id を DB に書き込む | adapter / repository 層 | D-API-SEP-draft 参照 |
| event_id の再生成 | **禁止** | replay 時も元の event_id を使う。adapter / projector は受け取った event_id を使い、再生成しない |

---

## §4 correlation_id 発行・継承

### 4.1 correlation_id の役割

`correlation_id` は cross-db trace に必須のフィールドである (ADR-018 §Decision.1 / L1-REQUIREMENTS.md §3.9 FR-DB-SEP-01)。

単一の CLI command / user request が orchestration / vmodel / scrum の複数 db にまたがって event を書き込む際、それらすべての event が同一の `correlation_id` を持つことで、後から `SELECT * WHERE correlation_id = ?` で 1 つの request に関連する全 event を横断取得できる。

### 4.2 発行ルール

| ルール | 内容 |
|---|---|
| 発行起点 | orchestration.db の top-level event (CLI command entry point) で新規発行 |
| 継承 | 同一 CLI command 内で vmodel.db / scrum.db に書き込む event は orchestration の correlation_id を継承 |
| 同一 request 内の全 event | 同一 `correlation_id` を共有する |
| 入れ子 command | 子 command は親の correlation_id を受け取り継承する。新規発行しない |

### 4.3 継承 API（historical / superseded）

> historical / superseded: `threading.local` ベースの API 仕様は履歴参照。normative contract は §4.6 の `contextvars` 実装のみとし、`2026-05-18 merge` 時点で上位節へ統合した。

```python
# cli/lib/event_envelope.py
# @helix:index id=event-envelope.correlation_context domain=cli/lib
#   summary=correlation_id を thread-local で管理する context manager
#   対応設計: D-CONTRACT-EVENT-draft-v0.1 §4.3

from contextlib import contextmanager
from typing import Iterator, Optional
import threading

_correlation_context = threading.local()


def get_current_correlation_id() -> Optional[str]:
    """現在の thread-local context から correlation_id を取得する。

    Returns:
        str | None: 現在の correlation_id。context 外では None。
    """
    return getattr(_correlation_context, "correlation_id", None)


@contextmanager
def correlation_context(parent: Optional[str] = None) -> Iterator[str]:
    """correlation_id を thread-local context で管理する context manager。

    Args:
        parent: 継承元 correlation_id。
            - None (default): 新規発行 (orchestration top-level event の起点)
            - 文字列: 既存 correlation_id を継承 (vmodel / scrum の event)

    Yields:
        str: 有効な correlation_id (発行 or 継承)

    Example:
        # orchestration.db top-level: 新規発行
        with correlation_context() as corr_id:
            # corr_id = 新規 UUID v7
            write_orchestration_event(corr_id=corr_id)
            # 同一 with ブロック内で vmodel.db にも書き込む
            with correlation_context(parent=corr_id) as child_corr_id:
                # child_corr_id == corr_id (継承)
                write_vmodel_event(corr_id=child_corr_id)

    Note:
        実装本体は Phase 4.B carry (§7 #3)。本 L3 は API signature のみ確定。
    """
    raise NotImplementedError("Phase 4.B で実装 (carry)")
```

### 4.4 cross-db trace の具体例

```
# CLI: helix gate pass G2
# ↓
# orchestration.db: gate.passed event を発行
#   event_id      = "018f4a1b-..."   (新規 UUID v7)
#   correlation_id = "corr-018f4a1b-..." (新規発行)
#   aggregate_type = "gate"
#   event_type     = "gate.passed"
#
# 同 command 内: vmodel.db に artifact event を書き込む
#   event_id      = "018f4a1c-..."   (別の UUID v7)
#   correlation_id = "corr-018f4a1b-..." (orchestration の correlation_id を継承)
#   aggregate_type = "artifact"
#   event_type     = "artifact.linked"
#
# 後で cross-db trace:
# SELECT * FROM event_envelope
#   WHERE correlation_id = 'corr-018f4a1b-...'
# → orchestration.db と vmodel.db の 2 event が返る
```

D-API-SEP-draft §4 の cross-db read helper (`read_cross_db_projection`) は projection_state 経由の snapshot 参照であり、correlation_id による event trace とは用途が異なる。event trace 専用の `query_events_by_correlation_id` helper は Phase 4.B で検討する (carry §7 #7)。

### 4.5 correlation_id format (Phase 4.B 確定 carry)

現時点では UUID v7 形式を基本とする。短縮 hash (12 文字、人間可読性優先) との選択は以下の観点で Phase 4.B に持ち越す:

| 比較軸 | UUID v7 形式 | 短縮 hash 12 文字 |
|---|---|---|
| global uniqueness | 強保証 | 衝突リスクあり (DB UNIQUE 制約で検出は可能) |
| 人間可読性 | 低 (36 文字) | 高 (12 文字) |
| log 可読性 | 冗長 | 簡潔 |
| 実装コスト | generate_event_id() と共通 | 別実装が必要 |

---

### 4.6 contextvars normalize 仕様（Phase 4.B freeze 取り込み）

`threading.local` 記述ではなく `contextvars` を採用し、`cli/lib/correlation_context.py` の実装に整合する。
```python
"""Correlation context helpers for cross-db trace propagation."""

import contextvars
from contextlib import contextmanager
from typing import Iterator

from . import uuid7_generator

_CORRELATION_CONTEXT: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "helix_correlation_id",
    default=None,
)


def current_correlation_id() -> str | None:
    return _CORRELATION_CONTEXT.get()


def get_current_correlation_id() -> str | None:
    return current_correlation_id()


@contextmanager
def correlation_context(parent: str | None = None) -> Iterator[str]:
    correlation_id = parent if parent is not None else uuid7_generator.generate_event_id()
    token = _CORRELATION_CONTEXT.set(correlation_id)
    try:
        yield correlation_id
    finally:
        _CORRELATION_CONTEXT.reset(token)
```

実装一致条件:

- `current_correlation_id()` は `get_current_correlation_id()` の alias 参照と互換
- `correlation_context(parent=None)` は新規 correlation_id を発行
- `correlation_context(parent=<id>)` は継承 context を返却
- `clear_correlation()` は context 終了時リセットとして扱う（token restore）

`D-API-SEP-phase4b-addendum` の §F と互換整合し、`docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` 側は実装正本として contextvars を確定する。
### 4.7 read / write の context 規約（補足）

- `read_cross_db_projection()` を含む read 時も、`correlation_context` で発行された correlation_id を引き継ぐ
- thread を跨いだ実行時は `contextvars` により呼び出し元 context へ依存

### 4.8 correlation API（互換名）
- `set_correlation(correlation_id: str | None) -> str | None`: exported API ではない alias 規約。`current_correlation_id()` 系と同義で、実装は `_CORRELATION_CONTEXT.set(...)`（`ContextVar.set`）経由で語義を持つ。
- `get_correlation() -> str | None`: exported API ではない alias 規約。`get_current_correlation_id()` と同一意味で、本文の実装名は `current_correlation_id() / get_current_correlation_id()` を主契約とする。
- `clear_correlation()`: exported API ではない alias 規約。`correlation_context` の終了時に行う `ContextVar.reset(token)` 相当（`ContextVar` トークンの復元）でクリア扱い。
## §5 payload schema 規約

### 5.1 payload の型と基本規約

`payload` は `dict[str, Any]` として `EventEnvelope` に保存し、SQLite には JSON 文字列として格納する (`to_sqlite_row` で `json.dumps()`)。

基本規約:
- JSON serializable であること (`json.dumps()` で例外が出ないこと)
- 空 dict `{}` は許可 (event 発生自体が情報を持つ場合)
- 巨大な payload (> 1MB 相当) は禁止。event log は append-only で肥大化するため、バイナリ / 大量データは別ストレージに保存し payload に参照 URL / path を持つ設計を推奨

### 5.2 event_type 命名規約

```
<aggregate_type>.<verb_past>
```

| 要素 | ルール | 例 |
|---|---|---|
| aggregate_type | db_name と対応する aggregate 種別 | `phase` / `gate` / `artifact` / `hypothesis` |
| verb_past | 過去形動詞 (event 確定済を表す) | `transitioned` / `passed` / `created` / `linked` |
| separator | `.` (ドット) | `phase.transitioned` |
| 禁止 | 現在形 / 命令形 | `phase.transition` / `gate.pass` (禁止) |

**db 別 aggregate_type 例**:

| db | aggregate_type 例 | event_type 例 |
|---|---|---|
| orchestration | `phase` / `gate` / `agent_slot` | `phase.transitioned` / `gate.passed` / `agent_slot.released` |
| vmodel | `artifact` / `artifact_link` / `drive_decision` | `artifact.created` / `artifact.linked` / `drive_decision.recorded` |
| scrum | `hypothesis` / `scrum_loop` / `srf_chain` | `hypothesis.confirmed` / `scrum_loop.started` / `srf_chain.bridged` |

### 5.3 payload schema 管理方針

```
cli/lib/events/schemas/
  phase.transitioned.json
  gate.passed.json
  artifact.created.json
  hypothesis.confirmed.json
  ... (Phase 4.B で event_type ごとに起票)
```

- 配置: `cli/lib/events/schemas/<event_type>.json` (ドットをファイル名に含む)
- format: JSON Schema Draft-07
- 本 L3 doc は規約のみ。具体的な schema ファイルは Phase 4.B で Codex se が起票する

### 5.4 schema 進化の原則

| 原則 | 内容 |
|---|---|
| backward compatible only | 既存 field の削除 / 型変更は禁止 (append-only event log を破壊する) |
| additive only | 新 field は optional として追加する。既存 consumer が unknown field を ignore するよう実装する |
| breaking change | 新 event_type として採番する (例: `phase.transitioned.v2`)。旧 event_type は deprecate マークのみ |

### 5.5 payload schema の例

```json
// cli/lib/events/schemas/phase.transitioned.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "phase.transitioned",
  "description": "HELIX フェーズ遷移 event の payload schema",
  "type": "object",
  "required": ["from_phase", "to_phase", "owner"],
  "additionalProperties": false,
  "properties": {
    "from_phase": {
      "type": "string",
      "description": "遷移前フェーズ (例: 'L3')"
    },
    "to_phase": {
      "type": "string",
      "description": "遷移後フェーズ (例: 'L4')"
    },
    "owner": {
      "type": "string",
      "description": "フェーズ遷移を実行したエージェント / ロール (例: 'pm-opus')"
    },
    "reason": {
      "type": "string",
      "description": "遷移理由 (optional)"
    }
  }
}
```

```json
// cli/lib/events/schemas/gate.passed.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "gate.passed",
  "description": "HELIX ゲート通過 event の payload schema",
  "type": "object",
  "required": ["gate_name", "plan_id"],
  "additionalProperties": false,
  "properties": {
    "gate_name": {
      "type": "string",
      "enum": ["G1", "G1.5", "G1R", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11"]
    },
    "plan_id": {
      "type": "string",
      "description": "ゲートと対応する PLAN ID (例: 'PLAN-084')"
    },
    "evidence": {
      "type": "string",
      "description": "通過根拠の記述 (optional)"
    }
  }
}
```

---

## §6 occurred_at 規約

### 6.1 format 仕様

| 項目 | 規約 |
|---|---|
| format | ISO8601 UTC (`datetime.now(timezone.utc).isoformat()` の出力形式) |
| 例 | `'2026-05-17T18:50:00.123456+00:00'` |
| timezone | UTC 固定 (local time 禁止) |
| precision | マイクロ秒 (Python `datetime.isoformat()` のデフォルト) |

### 6.2 生成方法

```python
from datetime import datetime, timezone

occurred_at: str = datetime.now(timezone.utc).isoformat()
# → '2026-05-17T18:50:00.123456+00:00'
```

`create_event_envelope()` factory (§2.4) が `occurred_at` を生成するため、呼び出し側は指定不要。

### 6.3 occurred_at と record 時刻の区別

| 項目 | 内容 |
|---|---|
| `occurred_at` | event が **発生した** 時刻。CLI command 実行中の `datetime.now(timezone.utc)` |
| record 時刻 | SQLite が **INSERT した** 時刻。`CURRENT_TIMESTAMP` または SQLite `DEFAULT` |
| 用途の違い | `occurred_at` は audit trail / replay の基準時刻。record 時刻は DB insert latency の計測用 |
| D-DB-SEP-draft の設計 | event_envelope table は `occurred_at` を持ち、record 時刻は `created_at DATETIME DEFAULT CURRENT_TIMESTAMP` として別 column に保持する |

### 6.4 timezone 固定の理由

| 理由 | 詳細 |
|---|---|
| cross-region audit trail | HELIX が複数 timezone の環境で動作する場合、local time では audit trail の ORDER BY が狂う |
| cross-db correlation | orchestration / vmodel / scrum の event を `occurred_at` でソートする際、timezone が混在すると順序が不定になる |
| projector replay | replay 時の event ordering は `occurred_at` の UTC 値を基準にする。local time は DST 変更時に逆転する |

---

## §7 carry to Phase 4

本 L3 draft で確定した API signature と規約を受けて、Phase 4 で実装する作業を以下に割り当てる。

| # | carry 項目 | 確定 phase | 担当 | 依存 |
|---|---|---|---|---|
| 1 | UUID v7 generator 実装 (uuid7 パッケージ採用 or 自前実装) | Phase 4.A | Codex se | Python バージョン確認 |
| 2 | `EventEnvelope` dataclass 実装 (`to_sqlite_row` / `from_sqlite_row` + `db_name` validation) | Phase 4.B | Codex se | carry #1 |
| 3 | `create_event_envelope()` factory 実装 (db_name validation + generate_event_id 呼び出し) | Phase 4.B | Codex se | carry #1, #2 |
| 4 | `correlation_context` context manager 実装 (thread-local) | Phase 4.B | Codex se | carry #2 |
| 5 | event_type 別 payload JSON schema 起票 (`cli/lib/events/schemas/*.json`) | Phase 4.B | Codex se | carry #2 |
| 6 | payload validator 実装 (event_type → JSON schema → jsonschema.validate) | Phase 4.B | Codex se | carry #5 |
| 7 | `EventEnvelope` unit test (`frozen` / `db_name` validation / `to_sqlite_row` round-trip) | Phase 4.B | Codex qa | carry #2, #3 |
| 8 | `correlation_id` cross-db trace integration test | Phase 4.B | Codex qa | carry #4 |
| 9 | UUID v7 collision rate / performance benchmark (HELIX scale 評価) | Phase 4.A | Codex perf | carry #1 |
| 10 | `query_events_by_correlation_id` helper 実装 (cross-db event 検索) | Phase 4.B | Codex se | carry #4 |
| 11 | Pydantic 移行検討 (HELIX 全体での Pydantic 採用判断が前提) | Phase 6+ | PM | HELIX 方針確定 |

---

## §8 V-model trace

本文書は HELIX_CORE.md §V-model 4 artifact 双方向 trace 原則に準拠し、4 artifact (設計 / 実装コード / テスト設計 / テストコード) の対応関係を以下に明示する。

### 4 artifact 対応表

| Artifact | 文書 / ファイル | 状態 |
|---|---|---|
| ① 設計 (本文書) | `docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` | Phase 3 draft |
| ② 実装コード | `cli/lib/event_envelope.py` / `cli/lib/correlation_context.py` | Phase 4.B 実装 (carry) |
| ③ 単体テスト設計 | `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` §3 (U-EVT-001〜010) + §4 (U-UUID-001〜005) + §5 (U-CORR-001〜005) | Phase 3.4 起票済 (commit ff04129) |
| ③ 結合テスト設計 | `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` §5 (I-CORR-001〜006) | Phase 3.4 起票済 (commit ff04129) |
| ④ 単体テストコード | `cli/lib/tests/test_event_envelope_unit.py` / `test_uuid7_generator_unit.py` / `test_correlation_context_unit.py` | Phase 4.B 起票 (carry) |
| ④ 結合テストコード | `cli/lib/tests/test_correlation_integration.py` | Phase 4.B 起票 (carry) |
| ④ テストコード | 上記テストファイルの実装 | Phase 4.B 実装 (carry) |

### 双方向 trace 宣言

- **本文書 → ② 実装コード**: 本文書 §2.2 の dataclass 定義が `cli/lib/event_envelope.py` の実装根拠。実装時に `# 対応設計: D-CONTRACT-EVENT-draft-v0.1 §2.2` を docstring に記載する
- **本文書 → ③ テスト設計**: `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` §3 (U-EVT) + §4 (U-UUID) + §5 (U-CORR) + `PLAN-084-integration-test-design.md` §5 (I-CORR) (Phase 3.4 起票済、commit ff04129、frontmatter `related_designs` で双方向 trace 完備)
- **本文書 → ④ テストコード**: Phase 4.B 着手時に `cli/lib/tests/test_event_envelope_unit.py` / `test_uuid7_generator_unit.py` / `test_correlation_context_unit.py` / `test_correlation_integration.py` に `# DoD 検証: PLAN-084-unit-test-design.md U-EVT-XXX / U-UUID-XXX / U-CORR-XXX` を記載する (Phase 4.B carry)
- **③ テスト設計 → 本文書**: `PLAN-084-unit-test-design.md` / `PLAN-084-integration-test-design.md` frontmatter `related_designs` に「D-CONTRACT-EVENT-draft-v0.1」明示済 (Phase 3.4 反映済)
- **② 実装 → D-DB-SEP-draft §3**: `to_sqlite_row` / `from_sqlite_row` の column 順序は D-DB-SEP-draft §3 の event_envelope table 定義に準拠することを docstring に記載する

Phase 4.B 着手前に 4 artifact 全件 + 双方向 trace の存在を確認すること (G4 チェック条件)。

---

## §9 References

| 参照先 | 参照箇所 | 本文書との関係 |
|---|---|---|
| ADR-018 §Decision.1 | event envelope 規約 (`event_id` / `aggregate_id` / `db_name` / `correlation_id` 等 8 field) | 本文書全体の根拠。ADR の規約を Python API に展開 |
| ADR-018 §Decision.2 | 6 軸判定 matrix (event-sourced 3 db + hybrid + state-store) | §1.3 で EventEnvelope 対象 db を 3 件に限定する根拠 |
| ADR-019 §Decision.1/2 | HELIX 二重らせん命名原則 (artifact strand / record strand) | §4 の correlation_id が record strand を cross-db で繋ぐ概念根拠 |
| D-DB-SEP-draft-v0.1 §3 | event_envelope table SQL schema (Phase 3.1 起票済) | 本文書 §2.2 dataclass の 1:1 対応元。schema 正本 |
| D-API-SEP-draft-v0.1 §4 | cross-db read helper (`read_cross_db_projection`) | §4.4 で統合点として参照。correlation trace と projection の用途区別 |
| PLAN-084 §2.2-2.6 | Event Sourcing 6 軸判定 matrix / entity ownership / projector 境界 | 本文書の前提判断の原出典 |
| PLAN-084 §2.3 | Event Sourcing 採用 6 軸判定 (tl-advisor Round 2-3 反映) | §3.1 UUID v7 採用根拠および §1.3 db 範囲確認の根拠 |
| L1-REQUIREMENTS.md §3.9 FR-DB-SEP-01 | 6 db 物理分離 + entity ownership + cross-db 規約 | §1.4 aggregate_id identity 規約の受入条件 |
| L1-REQUIREMENTS.md §3.9 FR-DB-SEP-02 | Event Sourcing 6 軸判定 hybrid 採用 | §1.3 対象 db の範囲確認の受入条件 |
| D-CONTRACT-draft (PLAN-070) | 前段 D-CONTRACT (mock_to_implementation / functional_freeze 契約) | 本文書は EVENT 専用として extends する。前段 CONTRACT の規約は引き継ぎ D-CONTRACT-draft が正本 |
