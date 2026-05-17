#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

try:
    from . import compatibility_adapter, helix_db
except ImportError:  # pragma: no cover
    import helix_db
    REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from cli.lib import compatibility_adapter
    compatibility_adapter.helix_db = helix_db


ALLOWED_AGENT_KINDS = ("codex", "claude_subagent")
ALLOWED_RELEASE_STATUSES = ("completed", "failed", "cancelled")
ALLOWED_SLOT_SOURCES = ("helix_codex", "pretooluse_hook")
ALLOWED_STATS_BY = ("hour", "role", "plan_id", "agent_kind")


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


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_non_negative_int(value: int, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _build_slot_key(agent_kind: str, role: str | None, subagent_type: str | None) -> str:
    if agent_kind == "codex":
        return f"codex:{role or 'unknown'}"
    return f"subagent:{subagent_type or 'unknown'}"


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


# @helix:index id=agent_slots.fire_slot domain=cli/lib summary=agent slot を fire して row id を返す
def fire_slot(
    agent_kind: str,
    role: str | None = None,
    subagent_type: str | None = None,
    plan_id: str | None = None,
    task_id: str | None = None,
    sprint: str | None = None,
    session_id: str | None = None,
    automation_run_id: int | None = None,
    slot_source: str = "helix_codex",
) -> int:
    """新規 slot を INSERT し、row id を返す。"""
    agent_kind = _validate_choice(agent_kind, "agent_kind", ALLOWED_AGENT_KINDS)
    slot_source = _validate_choice(slot_source, "slot_source", ALLOWED_SLOT_SOURCES)
    if automation_run_id is not None:
        automation_run_id = helix_db._validate_positive_int(automation_run_id, "automation_run_id")

    payload = {
        "slot_key": _build_slot_key(agent_kind, _clean_optional_text(role), _clean_optional_text(subagent_type)),
        "agent_kind": agent_kind,
        "role": _clean_optional_text(role),
        "subagent_type": _clean_optional_text(subagent_type),
        "plan_id": _clean_optional_text(plan_id),
        "task_id": _clean_optional_text(task_id),
        "sprint": _clean_optional_text(sprint),
        "session_id": _clean_optional_text(session_id),
        "automation_run_id": automation_run_id,
        "slot_source": slot_source,
    }
    columns = list(payload.keys())
    placeholders = ", ".join(["?"] * len(columns))
    with _compat_write_connection(None) as conn:
        cursor = conn.execute(
            f"INSERT INTO agent_slots ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )
        return int(cursor.lastrowid)


# @helix:index id=agent_slots.release_slot domain=cli/lib summary=running slot を terminal status へ release する
def release_slot(slot_id: int, status: str = "completed", exit_code: int | None = None) -> None:
    """slot を release する。"""
    slot_id = helix_db._validate_positive_int(slot_id, "slot_id")
    status = _validate_choice(status, "status", ALLOWED_RELEASE_STATUSES)
    if exit_code is not None and type(exit_code) is not int:
        raise ValueError("exit_code must be an integer or None")

    with _compat_write_connection(None) as conn:
        row = conn.execute("SELECT status, released_at FROM agent_slots WHERE id = ?", (slot_id,)).fetchone()
        if row is None:
            raise ValueError(f"slot_id does not exist: {slot_id}")
        if row["status"] != "running" or row["released_at"] is not None:
            raise sqlite3.IntegrityError(f"slot is not running: {slot_id}")
        conn.execute(
            """
            UPDATE agent_slots
            SET released_at = datetime('now'),
                status = ?,
                exit_code = ?
            WHERE id = ?
            """,
            (status, exit_code, slot_id),
        )


# @helix:index id=agent_slots.list_active_slots domain=cli/lib summary=active running slot 一覧を返す
def list_active_slots() -> list[dict]:
    """active slot 一覧を返す。"""
    with _compat_write_connection(None) as conn:
        rows = conn.execute(
            """
            SELECT * FROM agent_slots
            WHERE status = 'running' AND released_at IS NULL
            ORDER BY fired_at ASC, id ASC
            """
        ).fetchall()
        return _rows_to_dicts(rows)


# @helix:index id=agent_slots.list_stale_slots domain=cli/lib summary=stale running slot 一覧を返す
def list_stale_slots(threshold_minutes: int = 5) -> list[dict]:
    """threshold を超えた running slot 一覧を返す。"""
    threshold_minutes = _validate_non_negative_int(threshold_minutes, "threshold_minutes")
    with _compat_write_connection(None) as conn:
        rows = conn.execute(
            """
            SELECT * FROM agent_slots
            WHERE status = 'running'
              AND released_at IS NULL
              AND fired_at <= datetime('now', ?)
            ORDER BY fired_at ASC, id ASC
            """,
            (f"-{threshold_minutes} minutes",),
        ).fetchall()
        return _rows_to_dicts(rows)


# @helix:index id=agent_slots.get_stats domain=cli/lib summary=agent slot 集計を group 軸ごとに返す
def get_stats(days: int = 7, by: str = "hour") -> list[dict]:
    """group 軸ごとの slot 集計を返す。"""
    days = _validate_non_negative_int(days, "days")
    by = _validate_choice(by, "by", ALLOWED_STATS_BY)
    group_expr = {
        "hour": "strftime('%Y-%m-%d %H:00:00', fired_at)",
        "role": "COALESCE(role, '(none)')",
        "plan_id": "COALESCE(plan_id, '(none)')",
        "agent_kind": "COALESCE(agent_kind, '(none)')",
    }[by]
    with _compat_write_connection(None) as conn:
        rows = conn.execute(
            f"""
            WITH base AS (
                SELECT
                    id,
                    {group_expr} AS group_value,
                    status,
                    fired_at,
                    COALESCE(released_at, datetime('now')) AS ended_at,
                    CAST(strftime('%s', COALESCE(released_at, datetime('now'))) AS INTEGER)
                      - CAST(strftime('%s', fired_at) AS INTEGER) AS duration_s
                FROM agent_slots
                WHERE fired_at >= datetime('now', ?)
            ),
            overlaps AS (
                SELECT
                    a.id,
                    a.group_value,
                    (
                        SELECT COUNT(*)
                        FROM base b
                        WHERE b.group_value = a.group_value
                          AND b.fired_at <= a.ended_at
                          AND b.ended_at >= a.fired_at
                    ) AS concurrent_count
                FROM base a
            )
            SELECT
                base.group_value AS "group",
                COUNT(*) AS total,
                COALESCE(MAX(overlaps.concurrent_count), 0) AS peak_parallel,
                ROUND(AVG(base.duration_s), 2) AS avg_duration_s,
                SUM(CASE WHEN base.status = 'running' THEN 1 ELSE 0 END) AS running,
                SUM(CASE WHEN base.status = 'completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN base.status = 'failed' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN base.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
            FROM base
            LEFT JOIN overlaps ON overlaps.id = base.id
            GROUP BY base.group_value
            ORDER BY base.group_value ASC
            """,
            (f"-{days} days",),
        ).fetchall()
        return _rows_to_dicts(rows)
