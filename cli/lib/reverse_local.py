#!/usr/bin/env python3
from __future__ import annotations

import json
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


LOOP_PREFIX = "RL-"
ALLOWED_STATES = ("R0", "R1", "R2", "R3", "R4")
ALLOWED_TARGET_LAYERS = ("L1", "L2", "L3", "L4")
ALLOWED_REVERSE_TYPES = ("scrum-to-forward",)
NEXT_STATE_BY_CURRENT = {
    "R0": "R1",
    "R1": "R2",
    "R2": "R3",
    "R3": "R4",
}


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


def _validate_loop_id(loop_id: str) -> str:
    value = _require_non_empty(loop_id, "loop_id")
    if not value.startswith(LOOP_PREFIX):
        raise ValueError(f"invalid loop_id: {loop_id}")
    return value


def _validate_reverse_type(reverse_type: str) -> str:
    value = _require_non_empty(reverse_type, "reverse_type")
    if value not in ALLOWED_REVERSE_TYPES:
        raise ValueError(f"invalid reverse_type: {reverse_type}")
    return value


def _validate_target_layer(target_layer: str) -> str:
    value = _require_non_empty(target_layer, "target_layer")
    if value not in ALLOWED_TARGET_LAYERS:
        raise ValueError(f"invalid target_layer: {target_layer}")
    return value


def _validate_non_negative_int(value: int, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def _fetch_reverse_loop(conn: sqlite3.Connection, loop_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM reverse_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
    if row is None:
        raise ValueError(f"loop_id does not exist: {loop_id}")
    return row


def _fetch_confirmed_scrum_loop(conn: sqlite3.Connection, scrum_loop_id: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT * FROM scrum_local_loops
        WHERE loop_id = ? AND state = 'S3' AND decide_result = 'confirmed'
        """,
        (_require_non_empty(scrum_loop_id, "scrum_loop_id"),),
    ).fetchone()
    if row is None:
        raise ValueError(f"confirmed scrum loop does not exist: {scrum_loop_id}")
    return row


def _next_loop_id(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT loop_id FROM reverse_local_loops WHERE loop_id LIKE ? ORDER BY loop_id ASC",
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
        actor="reverse_local",
        payload={"action": action, **payload},
    )


# @helix:index id=reverse_local.init_from_scrum domain=cli/lib summary=confirmed scrum loop から SRF chain を初期化する
def init_from_scrum(scrum_loop_id: str, reverse_type: str = "scrum-to-forward") -> str:
    """confirmed scrum loop を起点に reverse loop を作成する。"""
    reverse_type = _validate_reverse_type(reverse_type)
    with _compat_write_connection(None) as conn:
        scrum_row = _fetch_confirmed_scrum_loop(conn, scrum_loop_id)
        loop_id = _next_loop_id(conn)
        conn.execute(
            """
            INSERT INTO reverse_local_loops (loop_id, parent_scrum_loop_id, reverse_type)
            VALUES (?, ?, ?)
            """,
            (loop_id, scrum_row["loop_id"], reverse_type),
        )
        _record_audit_event(
            conn,
            "init_from_scrum",
            {
                "loop_id": loop_id,
                "parent_scrum_loop_id": scrum_row["loop_id"],
                "reverse_type": reverse_type,
            },
        )
        return loop_id


# @helix:index id=reverse_local.transition_state domain=cli/lib summary=reverse loop を逐次状態遷移させる
def transition_state(loop_id: str, new_state: str) -> None:
    """R0→R1→R2→R3→R4 の逐次遷移のみ許可する。"""
    loop_id = _validate_loop_id(loop_id)
    new_state = _require_non_empty(new_state, "new_state")
    if new_state not in ALLOWED_STATES:
        raise ValueError(f"invalid new_state: {new_state}")

    with _compat_write_connection(None) as conn:
        row = _fetch_reverse_loop(conn, loop_id)
        current_state = str(row["state"])
        expected_next = NEXT_STATE_BY_CURRENT.get(current_state)
        if expected_next != new_state:
            raise ValueError(f"invalid state transition: {current_state} -> {new_state}")
        conn.execute(
            "UPDATE reverse_local_loops SET state = ? WHERE loop_id = ?",
            (new_state, loop_id),
        )
        _record_audit_event(
            conn,
            "transition_state",
            {"loop_id": loop_id, "from_state": current_state, "to_state": new_state},
        )


# @helix:index id=reverse_local.route_to_forward domain=cli/lib summary=R4 reverse loop の Forward 合流先を確定する
def route_to_forward(
    loop_id: str,
    target_plan: str,
    target_layer: str,
    artifact_links: list[dict] | None = None,
) -> None:
    """R4 の reverse loop に Forward routing 情報を記録する。"""
    loop_id = _validate_loop_id(loop_id)
    target_plan = _require_non_empty(target_plan, "target_plan")
    target_layer = _validate_target_layer(target_layer)
    if artifact_links is not None:
        if not isinstance(artifact_links, list):
            raise ValueError("artifact_links must be a list of dict")
        for item in artifact_links:
            if not isinstance(item, dict):
                raise ValueError("artifact_links must contain dict items")
    serialized_links = None if artifact_links is None else json.dumps(artifact_links, ensure_ascii=False)

    with _compat_write_connection(None) as conn:
        row = _fetch_reverse_loop(conn, loop_id)
        if row["state"] != "R4":
            raise ValueError(f"loop state must be R4: {loop_id}")
        conn.execute(
            """
            UPDATE reverse_local_loops
            SET target_forward_plan = ?,
                target_forward_layer = ?,
                artifact_links = ?,
                routed_at = datetime('now')
            WHERE loop_id = ?
            """,
            (target_plan, target_layer, serialized_links, loop_id),
        )
        _record_audit_event(
            conn,
            "route_to_forward",
            {
                "loop_id": loop_id,
                "target_plan": target_plan,
                "target_layer": target_layer,
                "artifact_links": artifact_links,
            },
        )


# @helix:index id=reverse_local.list_active_loops domain=cli/lib summary=完了していない reverse loop 一覧を返す
def list_active_loops() -> list[dict]:
    """state != R4 の active reverse loop 一覧を返す。"""
    with _compat_write_connection(None) as conn:
        rows = conn.execute(
            """
            SELECT * FROM reverse_local_loops
            WHERE state != 'R4'
            ORDER BY started_at ASC, loop_id ASC
            """
        ).fetchall()
        return _rows_to_dicts(rows)


# @helix:index id=reverse_local.get_routing_stats domain=cli/lib summary=Forward 合流先 layer ごとの集計を返す
def get_routing_stats(days: int = 7) -> dict:
    """指定期間の routing layer 集計を返す。"""
    days = _validate_non_negative_int(days, "days")
    layers: dict[str, int] = {}
    with _compat_write_connection(None) as conn:
        rows = conn.execute(
            """
            SELECT target_forward_layer, COUNT(*) AS count
            FROM reverse_local_loops
            WHERE routed_at IS NOT NULL
              AND routed_at >= datetime('now', ?)
            GROUP BY target_forward_layer
            ORDER BY target_forward_layer ASC
            """,
            (f"-{days} days",),
        ).fetchall()
        for row in rows:
            layer = str(row["target_forward_layer"])
            layers[layer] = int(row["count"])
    total = sum(layers.values())
    return {"layers": layers, "total": total}
