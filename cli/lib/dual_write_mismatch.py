"""Dual-write mismatch detector for PLAN-084 Phase 4.B.6.

Design reference:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md §C
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

MAX_SAMPLE_SIZE = 1000
DETECTOR_AXIS_ID = "dual-write-mismatch"
DETECTOR_NAME = "check_dual_write_mismatch"
DETECTOR_PHASE_GATE = "Phase 4.B.6"
_VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _utc_now_iso8601() -> str:
    return datetime.now(timezone.utc).isoformat()


def _quote_identifier(identifier: str) -> str:
    if not _VALID_IDENTIFIER.fullmatch(identifier):
        raise ValueError(f"invalid SQLite identifier: {identifier!r}")
    return f'"{identifier}"'


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {_quote_identifier(table_name)}").fetchone()
    return int(row[0] if row else 0)


def _sample_limit(sample_size: int) -> int:
    if sample_size <= 0:
        raise ValueError("sample_size must be greater than 0")
    return min(int(sample_size), MAX_SAMPLE_SIZE)


def _primary_key_columns(conn: sqlite3.Connection, table_name: str) -> tuple[str, ...]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    pk_columns = sorted(
        (row[1], int(row[5]))
        for row in rows
        if int(row[5]) > 0
    )
    if pk_columns:
        return tuple(column for column, _ in pk_columns)
    return ("__helix_rowid__",)


def _key_from_row(row: dict[str, Any], pk_columns: tuple[str, ...]) -> str:
    if len(pk_columns) == 1:
        return str(row[pk_columns[0]])
    return json.dumps(
        {column: row[column] for column in pk_columns},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def _serialize_row(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)


def _sample_rows(
    conn: sqlite3.Connection,
    table_name: str,
    pk_columns: tuple[str, ...],
    sample_limit: int,
) -> dict[str, str]:
    if pk_columns == ("__helix_rowid__",):
        select_sql = (
            f"SELECT rowid AS __helix_rowid__, * "
            f"FROM {_quote_identifier(table_name)} "
            f'ORDER BY "__helix_rowid__" LIMIT ?'
        )
    else:
        order_by = ", ".join(_quote_identifier(column) for column in pk_columns)
        select_sql = (
            f"SELECT * FROM {_quote_identifier(table_name)} "
            f"ORDER BY {order_by} LIMIT ?"
        )

    cursor = conn.execute(select_sql, (sample_limit,))
    column_names = [column[0] for column in cursor.description or ()]
    rows: dict[str, str] = {}
    for values in cursor.fetchall():
        row = dict(zip(column_names, values))
        rows[_key_from_row(row, pk_columns)] = _serialize_row(row)
    return rows


def _database_path(conn: sqlite3.Connection) -> str:
    row = conn.execute("PRAGMA database_list").fetchone()
    if not row:
        return ":memory:"
    path = row[2]
    return str(path or ":memory:")


def _record_result(
    conn: sqlite3.Connection,
    result: MismatchResult,
    *,
    sample_limit: int,
) -> None:
    if not _table_exists(conn, "detector_runs"):
        raise RuntimeError("detector_runs table is required; apply v32 migration before recording mismatch results")

    findings = []
    if result.detected:
        findings.append(
            {
                "table_name": result.table_name,
                "legacy_row_count": result.legacy_row_count,
                "new_row_count": result.new_row_count,
                "mismatch_keys": list(result.mismatch_keys),
                "severity": result.severity,
            }
        )

    should_commit = not conn.in_transaction
    conn.execute(
        """
        INSERT INTO detector_runs (
            recorded_at, axis_id, detector_name, phase_gate, verdict,
            findings_json, cost_ms, raw_json, config_json, command, db_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.detected_at,
            DETECTOR_AXIS_ID,
            DETECTOR_NAME,
            DETECTOR_PHASE_GATE,
            "failed" if result.detected else "passed",
            json.dumps(findings, ensure_ascii=False, sort_keys=True),
            0,
            json.dumps(asdict(result), ensure_ascii=False, sort_keys=True),
            json.dumps(
                {"sample_size": sample_limit, "table_name": result.table_name},
                ensure_ascii=False,
                sort_keys=True,
            ),
            DETECTOR_NAME,
            _database_path(conn),
        ),
    )
    if should_commit:
        conn.commit()


# @helix:index id=dual-write-mismatch.result domain=cli/lib summary=dual-write mismatch 判定結果 dataclass
@dataclass(frozen=True)
class MismatchResult:
    detected: bool
    table_name: str
    legacy_row_count: int
    new_row_count: int
    mismatch_keys: list[str]
    detected_at: str
    severity: str


# @helix:index id=dual-write-mismatch.check domain=cli/lib summary=legacy/new db の dual-write mismatch を sample 比較し detector_runs へ記録する
def check_dual_write_mismatch(
    legacy_conn: sqlite3.Connection,
    new_conn: sqlite3.Connection,
    table_name: str,
    *,
    sample_size: int = 1000,
) -> MismatchResult:
    """Compare sampled rows between legacy and new SQLite tables.

    `severity` is constrained by the frozen contract to `"warn" | "critical"`.
    The function therefore uses `"warn"` as the non-fail-close level and upgrades
    to `"critical"` for row-count, missing-table, or sampled key-set divergence.
    """

    sample_limit = _sample_limit(sample_size)
    legacy_exists = _table_exists(legacy_conn, table_name)
    new_exists = _table_exists(new_conn, table_name)
    legacy_row_count = _count_rows(legacy_conn, table_name) if legacy_exists else 0
    new_row_count = _count_rows(new_conn, table_name) if new_exists else 0
    mismatch_keys: list[str] = []
    severity = "warn"

    if legacy_exists and new_exists:
        legacy_pk_columns = _primary_key_columns(legacy_conn, table_name)
        new_pk_columns = _primary_key_columns(new_conn, table_name)
        if legacy_pk_columns != new_pk_columns:
            mismatch_keys = ["__primary_key_schema__"]
            severity = "critical"
        else:
            legacy_rows = _sample_rows(legacy_conn, table_name, legacy_pk_columns, sample_limit)
            new_rows = _sample_rows(new_conn, table_name, new_pk_columns, sample_limit)

            legacy_keys = set(legacy_rows)
            new_keys = set(new_rows)
            for key in sorted(legacy_keys ^ new_keys):
                mismatch_keys.append(key)

            for key in sorted(legacy_keys & new_keys):
                if legacy_rows[key] != new_rows[key]:
                    mismatch_keys.append(key)

            if legacy_row_count != new_row_count or legacy_keys != new_keys:
                severity = "critical"
    else:
        mismatch_keys = ["__missing_table__"]
        severity = "critical"

    detected = legacy_row_count != new_row_count or bool(mismatch_keys)
    result = MismatchResult(
        detected=detected,
        table_name=table_name,
        legacy_row_count=legacy_row_count,
        new_row_count=new_row_count,
        mismatch_keys=mismatch_keys,
        detected_at=_utc_now_iso8601(),
        severity=severity,
    )
    _record_result(new_conn, result, sample_limit=sample_limit)
    return result


__all__ = ["MismatchResult", "check_dual_write_mismatch"]
