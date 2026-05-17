"""Shadow replay helpers for PLAN-084 Phase 4.C.

This module replays legacy ``event_envelope`` rows into the shadow 6-db layout
and verifies derived projector state against legacy ``projection_state`` snapshots.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .event_envelope import from_sqlite_row
from .migrations import v31_db_separation
from .projectors import PROJECTORS


_PROJECTORS_BY_DB = {
    projector.target_db: projector for projector in PROJECTORS.values()
}


# @helix:index id=shadow-replay.replay-result domain=cli/lib summary=replay 実行結果を返す dataclass 定義
@dataclass(frozen=True)
class ReplayResult:
    replayed_count: int
    skipped_count: int
    failed_count: int
    mismatches: list[dict]
    started_at: str
    completed_at: str


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_projection_state_table(conn: sqlite3.Connection) -> None:
    conn.execute(v31_db_separation.PROJECTION_STATE_SCHEMA)


def _load_legacy_state(conn: sqlite3.Connection) -> dict[tuple[str, str], dict]:
    row = conn.execute(
        """
        SELECT projector_id, db_name, last_processed_event_id, snapshot
        FROM projection_state
        """
    ).fetchall()
    state: dict[tuple[str, str], dict] = {}
    for row_item in row:
        try:
            snapshot = None if row_item["snapshot"] is None else json.loads(row_item["snapshot"])
        except (TypeError, ValueError):
            snapshot = None
        state[(str(row_item["projector_id"]), str(row_item["db_name"]))] = {
            "last_processed_event_id": row_item["last_processed_event_id"],
            "snapshot": snapshot,
        }
    return state


def _shadow_db_path(base_path: str, db_name: str) -> str:
    root = Path(base_path)
    if root.suffix and root.is_file():
        # Backward-compat helper for direct file paths: place db under parent.
        root = root.parent
    if not root.exists():
        root = root.parent if str(root).endswith(".db") else root
    return str(root / f"{db_name}.db")


def _read_events(
    legacy_conn: sqlite3.Connection, *, since_event_id: str | None, replay_limit: int | None
) -> list[sqlite3.Row]:
    where_clause = ""
    params: list[object] = []
    if since_event_id:
        where_clause = "WHERE event_id > ?"
        params.append(since_event_id)

    sql = f"""
        SELECT event_id, aggregate_id, aggregate_type, db_name, event_type,
               payload, correlation_id, occurred_at
        FROM event_envelope
        {where_clause}
        ORDER BY occurred_at ASC, event_id ASC
    """
    rows = legacy_conn.execute(sql, params).fetchall()
    if replay_limit is not None:
        rows = rows[:replay_limit]
    return rows


def _open_shadow_connection(shadow_db_path: str, db_name: str) -> sqlite3.Connection:
    target_path = _shadow_db_path(shadow_db_path, db_name)
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    _ensure_projection_state_table(conn)
    return conn


def _legacy_projection_snapshot_key(
    legacy_states: dict[tuple[str, str], dict], projector_id: str, db_name: str
) -> dict | None:
    return legacy_states.get((projector_id, db_name))


def _snapshot_payload(snapshot: dict) -> dict[str, Any]:
    return dict(snapshot) if snapshot is not None else {}


def _build_mismatch(
    projector_id: str,
    db_name: str,
    *,
    reason: str,
    replayed_snapshot: dict | None,
    legacy_snapshot: dict | None,
    replayed_last_processed_event_id: str | None,
    legacy_last_processed_event_id: str | None,
) -> dict:
    return {
        "projector_id": projector_id,
        "db_name": db_name,
        "reason": reason,
        "replayed_snapshot": replayed_snapshot,
        "legacy_snapshot": legacy_snapshot,
        "replayed_last_processed_event_id": replayed_last_processed_event_id,
        "legacy_last_processed_event_id": legacy_last_processed_event_id,
    }


# @helix:index id=shadow-replay.replay-to-shadow-db domain=cli/lib summary=legacy event を shadow db に replay して mismatch を集約
def replay_to_shadow_db(
    legacy_conn: sqlite3.Connection,
    shadow_db_path: str,
    *,
    since_event_id: str | None = None,
    dry_run: bool = False,
) -> ReplayResult:
    """Replay legacy events and compare derived shadow state with legacy snapshots."""
    started_at = _timestamp_now()
    legacy_conn.row_factory = sqlite3.Row
    events = _read_events(legacy_conn, since_event_id=since_event_id, replay_limit=1000)
    legacy_states = _load_legacy_state(legacy_conn)

    replayed_count = 0
    skipped_count = 0
    failed_count = 0
    mismatches: list[dict] = []

    projector_state: dict[tuple[str, str], dict] = {}
    projector_last_event_id: dict[tuple[str, str], str] = {}

    target_conns: dict[str, sqlite3.Connection] = {}
    try:
        for row in events:
            envelope = from_sqlite_row(row)

            if envelope.db_name not in _PROJECTORS_BY_DB:
                skipped_count += 1
                continue

            projector = _PROJECTORS_BY_DB[envelope.db_name]
            projector_key = (projector.projector_id, envelope.db_name)
            current_snapshot = projector_state.get(
                projector_key, projector.initial_snapshot()
            )

            try:
                next_snapshot = projector.apply(envelope, current_snapshot)
                projector_state[projector_key] = next_snapshot
                projector_last_event_id[projector_key] = envelope.event_id
                replayed_count += 1
            except Exception as exc:
                failed_count += 1
                mismatches.append(
                    _build_mismatch(
                        projector.projector_id,
                        envelope.db_name,
                        reason=f"projector apply failed: {exc}",
                        replayed_snapshot=current_snapshot,
                        legacy_snapshot=None,
                        replayed_last_processed_event_id=envelope.event_id,
                        legacy_last_processed_event_id=None,
                    )
                )
                continue

            if dry_run:
                continue

            conn = target_conns.get(envelope.db_name)
            if conn is None:
                conn = _open_shadow_connection(shadow_db_path, envelope.db_name)
                target_conns[envelope.db_name] = conn

            conn.execute(
                """
                INSERT INTO projection_state(
                    projector_id, db_name, last_processed_event_id, snapshot, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(projector_id, db_name) DO UPDATE SET
                    last_processed_event_id = excluded.last_processed_event_id,
                    snapshot = excluded.snapshot,
                    updated_at = excluded.updated_at
                """,
                (
                    projector.projector_id,
                    envelope.db_name,
                    envelope.event_id,
                    json.dumps(_snapshot_payload(next_snapshot), ensure_ascii=False, sort_keys=True),
                    _timestamp_now(),
                ),
            )

        if not dry_run:
            for conn in target_conns.values():
                conn.commit()

    finally:
        for conn in target_conns.values():
            conn.close()

    for projector_key, replayed_state in projector_state.items():
        projector_id, db_name = projector_key
        legacy_state = _legacy_projection_snapshot_key(legacy_states, projector_id, db_name)
        if legacy_state is None:
            continue

        legacy_snapshot = legacy_state["snapshot"]
        legacy_last = legacy_state["last_processed_event_id"]
        replayed_last = projector_last_event_id.get(projector_key)

        if _snapshot_payload(legacy_snapshot) != _snapshot_payload(replayed_state):
            failed_count += 1
            mismatches.append(
                _build_mismatch(
                    projector_id,
                    db_name,
                    reason="snapshot mismatch",
                    replayed_snapshot=replayed_state,
                    legacy_snapshot=legacy_snapshot,
                    replayed_last_processed_event_id=replayed_last,
                    legacy_last_processed_event_id=legacy_last,
                )
            )
            continue

        if legacy_last != replayed_last:
            failed_count += 1
            mismatches.append(
                _build_mismatch(
                    projector_id,
                    db_name,
                    reason="last_processed_event_id mismatch",
                    replayed_snapshot=replayed_state,
                    legacy_snapshot=legacy_snapshot,
                    replayed_last_processed_event_id=replayed_last,
                    legacy_last_processed_event_id=legacy_last,
                )
            )

    completed_at = _timestamp_now()
    return ReplayResult(
        replayed_count=replayed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        mismatches=mismatches,
        started_at=started_at,
        completed_at=completed_at,
    )


__all__ = ["ReplayResult", "replay_to_shadow_db"]
