#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

try:
    from . import agent_slots, compatibility_adapter, helix_db
except ImportError:  # pragma: no cover
    import agent_slots
    import helix_db
    REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from cli.lib import compatibility_adapter
    compatibility_adapter.helix_db = helix_db


ALLOWED_EVENT_KINDS = ("pull", "push", "audit")
ALLOWED_SEVERITIES = ("info", "warning", "critical")


@contextmanager
def _compat_write_connection(db_path: str | None = None, ensure_schema: bool = True):
    generator = compatibility_adapter.write_connection.__wrapped__(db_path, ensure_schema)
    conn = next(generator)
    try:
        yield conn
    except BaseException as exc:
        try:
            generator.throw(exc)
        except StopIteration:
            pass
        raise
    else:
        try:
            next(generator)
        except StopIteration:
            pass


def _validate_choice(value: str, field_name: str, allowed_values: tuple[str, ...]) -> str:
    text = str(value).strip()
    if text not in allowed_values:
        raise ValueError(f"invalid {field_name}: {value}")
    return text


def _require_non_empty_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_non_negative_int(value: int, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _encode_payload(payload: dict | None) -> str | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict or None")
    return json.dumps(payload, ensure_ascii=False)


def _decode_payload(value: str | None) -> dict | None:
    if not value:
        return None
    decoded = json.loads(value)
    if decoded is None:
        return None
    if not isinstance(decoded, dict):
        raise ValueError("payload must decode to a dict")
    return decoded


def _row_to_event(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["payload"] = _decode_payload(item.get("payload"))
    item["user_visible"] = bool(item["user_visible"])
    return item


def _fetch_recent_events(
    conn: sqlite3.Connection,
    *,
    days: int,
    severity: str | None,
    session_id: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    where = []
    params: list[object] = []
    if days == 0:
        where.append("triggered_at >= datetime('now', 'start of day')")
    else:
        where.append("triggered_at >= datetime('now', ?)")
        params.append(f"-{days} days")
    if severity is not None:
        where.append("severity = ?")
        params.append(severity)
    if session_id is not None:
        where.append("session_id = ?")
        params.append(session_id)
    limit_sql = ""
    if limit is not None:
        limit_sql = " LIMIT ?"
        params.append(limit)
    rows = conn.execute(
        f"""
        SELECT *
        FROM harness_check_events
        WHERE {' AND '.join(where)}
        ORDER BY triggered_at DESC, id DESC
        {limit_sql}
        """,
        params,
    ).fetchall()
    return [_row_to_event(row) for row in rows]


def _query_running_tasks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, run_kind, trigger_actor, plan_id, started_at, status, summary
        FROM automation_runs
        WHERE status = 'running'
        ORDER BY started_at ASC, id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _query_peak_parallel_today(conn: sqlite3.Connection, session_id: str | None) -> int:
    where = ["fired_at >= datetime('now', 'start of day')"]
    params: list[object] = []
    if session_id is not None:
        where.append("session_id = ?")
        params.append(session_id)
    row = conn.execute(
        f"""
        WITH base AS (
            SELECT
                id,
                fired_at,
                COALESCE(released_at, datetime('now')) AS ended_at
            FROM agent_slots
            WHERE {' AND '.join(where)}
        ),
        overlaps AS (
            SELECT
                a.id,
                (
                    SELECT COUNT(*)
                    FROM base b
                    WHERE b.fired_at <= a.ended_at
                      AND b.ended_at >= a.fired_at
                ) AS concurrent_count
            FROM base a
        )
        SELECT COALESCE(MAX(concurrent_count), 0) AS peak_parallel_today
        FROM overlaps
        """,
        params,
    ).fetchone()
    return int(row["peak_parallel_today"]) if row is not None else 0


# @helix:index id=harness_monitor.record_event domain=cli/lib summary=harness check event を append-only で記録する
def record_event(
    event_kind: str,
    check_name: str,
    *,
    session_id: str | None = None,
    related_slot_id: int | None = None,
    plan_id: str | None = None,
    severity: str = "info",
    payload: dict | None = None,
    user_visible: bool = False,
) -> int:
    """harness check event を INSERT し、row id を返す。"""
    event_kind = _validate_choice(event_kind, "event_kind", ALLOWED_EVENT_KINDS)
    check_name = _require_non_empty_text(check_name, "check_name")
    severity = _validate_choice(severity, "severity", ALLOWED_SEVERITIES)
    if related_slot_id is not None:
        related_slot_id = helix_db._validate_positive_int(related_slot_id, "related_slot_id")
    row = {
        "event_kind": event_kind,
        "check_name": check_name,
        "session_id": _clean_optional_text(session_id),
        "related_slot_id": related_slot_id,
        "plan_id": _clean_optional_text(plan_id),
        "severity": severity,
        "payload": _encode_payload(payload),
        "user_visible": int(bool(user_visible)),
    }
    columns = list(row.keys())
    placeholders = ", ".join(["?"] * len(columns))
    with _compat_write_connection(None) as conn:
        cursor = conn.execute(
            f"INSERT INTO harness_check_events ({', '.join(columns)}) VALUES ({placeholders})",
            [row[column] for column in columns],
        )
        return int(cursor.lastrowid)


# @helix:index id=harness_monitor.get_active_status domain=cli/lib summary=active harness status summary を返す
def get_active_status(session_id: str | None = None) -> dict:
    """active harness status summary を返す。"""
    session_id = _clean_optional_text(session_id)
    active_slots = agent_slots.list_active_slots()
    if session_id is not None:
        active_slots = [slot for slot in active_slots if slot.get("session_id") == session_id]
    with _compat_write_connection(None) as conn:
        return {
            "active_slot_count": len(active_slots),
            "running_tasks": _query_running_tasks(conn),
            "recent_warnings": _fetch_recent_events(
                conn,
                days=1,
                severity="warning",
                session_id=session_id,
                limit=10,
            ),
            "recent_criticals": _fetch_recent_events(
                conn,
                days=1,
                severity="critical",
                session_id=session_id,
                limit=10,
            ),
            "peak_parallel_today": _query_peak_parallel_today(conn, session_id),
        }


# @helix:index id=harness_monitor.get_session_audit domain=cli/lib summary=session 単位の harness event audit summary を返す
def get_session_audit(session_id: str) -> dict:
    """session 単位の harness event audit summary を返す。"""
    session_id = _require_non_empty_text(session_id, "session_id")
    with _compat_write_connection(None) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                COALESCE(SUM(CASE WHEN event_kind = 'pull' THEN 1 ELSE 0 END), 0) AS pull_count,
                COALESCE(SUM(CASE WHEN event_kind = 'push' THEN 1 ELSE 0 END), 0) AS push_count,
                COALESCE(SUM(CASE WHEN event_kind = 'audit' THEN 1 ELSE 0 END), 0) AS audit_count,
                COALESCE(SUM(CASE WHEN severity = 'info' THEN 1 ELSE 0 END), 0) AS info_count,
                COALESCE(SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END), 0) AS warning_count,
                COALESCE(SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END), 0) AS critical_count,
                MIN(triggered_at) AS first_event_at,
                MAX(triggered_at) AS last_event_at
            FROM harness_check_events
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        total_events = int(row["total_events"]) if row is not None else 0
        return {
            "session_id": session_id,
            "total_events": total_events,
            "by_kind": {
                "pull": int(row["pull_count"]) if row is not None else 0,
                "push": int(row["push_count"]) if row is not None else 0,
                "audit": int(row["audit_count"]) if row is not None else 0,
            },
            "by_severity": {
                "info": int(row["info_count"]) if row is not None else 0,
                "warning": int(row["warning_count"]) if row is not None else 0,
                "critical": int(row["critical_count"]) if row is not None else 0,
            },
            "first_event_at": row["first_event_at"] if row is not None else None,
            "last_event_at": row["last_event_at"] if row is not None else None,
        }


# @helix:index id=harness_monitor.list_recent_events domain=cli/lib summary=直近 N 日の harness event 一覧を返す
def list_recent_events(days: int = 1, severity: str | None = None) -> list[dict]:
    """直近 N 日の harness event 一覧を返す。"""
    days = _validate_non_negative_int(days, "days")
    if severity is not None:
        severity = _validate_choice(severity, "severity", ALLOWED_SEVERITIES)
    with _compat_write_connection(None) as conn:
        return _fetch_recent_events(conn, days=days, severity=severity)
