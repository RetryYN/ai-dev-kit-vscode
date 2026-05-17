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


LOOP_PREFIX = "H-LOCAL-"
ALLOWED_FORWARD_LAYERS = tuple(f"L{index}" for index in range(1, 12))
ALLOWED_STATES = ("S0", "S1", "S2", "S3")
ALLOWED_DECIDE_RESULTS = ("confirmed", "rejected", "pivot")


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


def _require_non_empty(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_forward_layer(forward_layer: str) -> str:
    layer = _require_non_empty(forward_layer, "forward_layer")
    if layer not in ALLOWED_FORWARD_LAYERS:
        raise ValueError(f"invalid forward_layer: {forward_layer}")
    return layer


def _validate_loop_id(loop_id: str) -> str:
    value = _require_non_empty(loop_id, "loop_id")
    if not value.startswith(LOOP_PREFIX):
        raise ValueError(f"invalid loop_id: {loop_id}")
    return value


def _validate_optional_positive_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    return helix_db._validate_positive_int(value, field_name)


def _validate_non_negative_int(value: int, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def _fetch_loop(conn: sqlite3.Connection, loop_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM scrum_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
    if row is None:
        raise ValueError(f"loop_id does not exist: {loop_id}")
    return row


def _assert_state(row: sqlite3.Row, expected_state: str) -> None:
    state = row["state"]
    if state != expected_state:
        raise ValueError(f"loop state must be {expected_state}: {row['loop_id']}")


def _next_loop_id(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT loop_id FROM scrum_local_loops WHERE loop_id LIKE ? ORDER BY loop_id ASC",
        (f"{LOOP_PREFIX}%",),
    ).fetchall()
    max_number = 0
    for row in rows:
        loop_id = str(row["loop_id"])
        suffix = loop_id[len(LOOP_PREFIX) :]
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))
    return f"{LOOP_PREFIX}{max_number + 1:03d}"


def _record_audit_event(conn: sqlite3.Connection, action: str, payload: dict) -> None:
    helix_db.insert_audit_log(
        conn,
        audit_kind="cli_invocation",
        actor="scrum_local",
        payload={"action": action, **payload},
    )


# @helix:index id=scrum_local.init_local_loop domain=cli/lib summary=UPS loop を初期化して H-LOCAL-NNN を返す
def init_local_loop(
    forward_layer: str,
    hypothesis: str,
    acceptance: str,
    forward_plan_id: str | None = None,
    parent_loop_id: str | None = None,
) -> str:
    """新規 UPS loop を state=S0 で作成する。"""
    layer = _validate_forward_layer(forward_layer)
    hypothesis = _require_non_empty(hypothesis, "hypothesis")
    acceptance = _require_non_empty(acceptance, "acceptance")
    forward_plan_id = _clean_optional_text(forward_plan_id)
    parent_loop_id = _clean_optional_text(parent_loop_id)

    with _compat_write_connection(None) as conn:
        if parent_loop_id is not None:
            _fetch_loop(conn, _validate_loop_id(parent_loop_id))
        loop_id = _next_loop_id(conn)
        conn.execute(
            """
            INSERT INTO scrum_local_loops (
                loop_id,
                forward_layer,
                forward_plan_id,
                hypothesis,
                acceptance,
                parent_loop_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (loop_id, layer, forward_plan_id, hypothesis, acceptance, parent_loop_id),
        )
        _record_audit_event(
            conn,
            "init_local_loop",
            {
                "loop_id": loop_id,
                "forward_layer": layer,
                "forward_plan_id": forward_plan_id,
                "parent_loop_id": parent_loop_id,
            },
        )
        return loop_id


# @helix:index id=scrum_local.record_poc domain=cli/lib summary=UPS loop を S0 から S1 へ進める
def record_poc(
    loop_id: str,
    commit_sha: str | None = None,
    agent_slot_id: int | None = None,
) -> None:
    """PoC 投入を記録し、loop を S1 に遷移させる。"""
    loop_id = _validate_loop_id(loop_id)
    commit_sha = _clean_optional_text(commit_sha)
    agent_slot_id = _validate_optional_positive_int(agent_slot_id, "agent_slot_id")

    with _compat_write_connection(None) as conn:
        row = _fetch_loop(conn, loop_id)
        _assert_state(row, "S0")
        conn.execute(
            """
            UPDATE scrum_local_loops
            SET state = 'S1',
                related_agent_slot_id = COALESCE(?, related_agent_slot_id)
            WHERE loop_id = ?
            """,
            (agent_slot_id, loop_id),
        )
        _record_audit_event(
            conn,
            "record_poc",
            {
                "loop_id": loop_id,
                "commit_sha": commit_sha,
                "agent_slot_id": agent_slot_id,
            },
        )


# @helix:index id=scrum_local.verify_loop domain=cli/lib summary=UPS loop を S1 から S2 へ進める
def verify_loop(loop_id: str, observation: str | None = None) -> None:
    """検証観測を記録し、loop を S2 に遷移させる。"""
    loop_id = _validate_loop_id(loop_id)
    observation = _clean_optional_text(observation)

    with _compat_write_connection(None) as conn:
        row = _fetch_loop(conn, loop_id)
        _assert_state(row, "S1")
        conn.execute("UPDATE scrum_local_loops SET state = 'S2' WHERE loop_id = ?", (loop_id,))
        _record_audit_event(
            conn,
            "verify_loop",
            {"loop_id": loop_id, "observation": observation},
        )


# @helix:index id=scrum_local.decide_loop domain=cli/lib summary=UPS loop を S2 から S3 へ進めて判定を記録する
def decide_loop(loop_id: str, result: str, note: str | None = None) -> None:
    """判定結果を記録し、loop を S3 に遷移させる。"""
    loop_id = _validate_loop_id(loop_id)
    result = _require_non_empty(result, "result")
    if result not in ALLOWED_DECIDE_RESULTS:
        raise ValueError(f"invalid result: {result}")
    note = _clean_optional_text(note)

    with _compat_write_connection(None) as conn:
        row = _fetch_loop(conn, loop_id)
        _assert_state(row, "S2")
        conn.execute(
            """
            UPDATE scrum_local_loops
            SET state = 'S3',
                decide_result = ?,
                decided_at = datetime('now')
            WHERE loop_id = ?
            """,
            (result, loop_id),
        )
        _record_audit_event(
            conn,
            "decide_loop",
            {"loop_id": loop_id, "result": result, "note": note},
        )


# @helix:index id=scrum_local.list_active_loops domain=cli/lib summary=完了していない UPS loop 一覧を返す
def list_active_loops(forward_layer: str | None = None) -> list[dict]:
    """state != S3 の active UPS loop 一覧を返す。"""
    layer = None if forward_layer is None else _validate_forward_layer(forward_layer)
    with _compat_write_connection(None) as conn:
        if layer is None:
            rows = conn.execute(
                """
                SELECT * FROM scrum_local_loops
                WHERE state != 'S3'
                ORDER BY started_at ASC, loop_id ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM scrum_local_loops
                WHERE state != 'S3' AND forward_layer = ?
                ORDER BY started_at ASC, loop_id ASC
                """,
                (layer,),
            ).fetchall()
        return _rows_to_dicts(rows)


# @helix:index id=scrum_local.get_stats domain=cli/lib summary=UPS decide_result の集計を返す
def get_stats(days: int = 7) -> dict:
    """指定期間の confirmed/rejected/pivot 集計を返す。"""
    days = _validate_non_negative_int(days, "days")
    counts = {result: 0 for result in ALLOWED_DECIDE_RESULTS}
    with _compat_write_connection(None) as conn:
        rows = conn.execute(
            """
            SELECT decide_result, COUNT(*) AS count
            FROM scrum_local_loops
            WHERE decide_result IS NOT NULL
              AND decided_at >= datetime('now', ?)
            GROUP BY decide_result
            """,
            (f"-{days} days",),
        ).fetchall()
        for row in rows:
            counts[str(row["decide_result"])] = int(row["count"])
    total = sum(counts.values())
    return {**counts, "total": total}
