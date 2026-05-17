"""Compatibility adapter for phased helix.db separation.

Design references:
- D-API-SEP-draft §2/§4
- D-API-SEP-phase4b-addendum §A
- D-DB-SEP-draft §5/§6
"""

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from sqlite3 import Connection
from typing import Any, Iterator
import inspect
import logging
import os

from . import helix_db
from .dual_write_connection import _DualWriteConnection

logger = logging.getLogger(__name__)

_FILE_TO_DB: dict[str, str] = {
    "agent_slots.py": "orchestration",
    "harness_monitor.py": "orchestration",
    "scrum_local.py": "scrum",
    "reverse_local.py": "scrum",
    "audit.py": "backend",
    "push_pr.py": "backend",
    "hooks.py": "backend",
    "telemetry.py": "backend",
    "helix-pr": "backend",
    "helix-push": "backend",
    "helix-agent": "orchestration",
}

_TABLE_PREFIX_TO_DB: dict[str, str] = {
    "phase_": "orchestration",
    "gate_": "orchestration",
    "sprint_": "orchestration",
    "agent_": "orchestration",
    "harness_": "orchestration",
    "artifact_": "vmodel",
    "test_design_": "vmodel",
    "hypothesis_": "scrum",
    "poc_": "scrum",
    "plan_": "plan",
    "task_": "plan",
    "wbs_": "plan",
    "automation_": "backend",
    "audit_": "backend",
    "session_": "backend",
}

_DB_NAME_TO_FILENAME: dict[str, str] = {
    "orchestration": "orchestration.db",
    "vmodel": "vmodel.db",
    "scrum": "scrum.db",
    "plan": "plan.db",
    "backend": "backend.db",
    "frontend": "frontend.db",
}

_KNOWN_PROJECTORS = frozenset({"phase_state", "artifact_chain", "hypothesis_state"})


def _is_discovery_mode() -> bool:
    return os.environ.get("HELIX_DB_DISCOVERY") == "1"


def _is_cutover_enabled() -> bool:
    return os.environ.get("HELIX_DB_CUTOVER") == "1"


def _resolve_helix_dir() -> Path:
    return Path(helix_db._resolve_db_path(None)).parent


def _validate_db_name(db_name: str) -> str:
    if db_name not in _DB_NAME_TO_FILENAME:
        raise RuntimeError(f"compatibility_adapter: unsupported db_name '{db_name}'")
    return db_name


def _discover_caller() -> tuple[str, str]:
    stack = inspect.stack(context=0)
    try:
        caller_frame = stack[2]
        return caller_frame.filename, caller_frame.function
    finally:
        del stack


# @helix:index id=compatibility-adapter.route-to-db domain=cli/lib summary=caller file から 6 db routing 判定
def _route_to_db(caller_file: str, caller_func: str) -> str:
    """Resolve the canonical target database from the caller context.

    File-based routing is authoritative. Function-name prefix routing is only a
    discovery fallback, because entity ownership must fail closed in
    production.
    """
    basename = Path(caller_file).name
    if basename in _FILE_TO_DB:
        return _FILE_TO_DB[basename]

    caller_func_lower = caller_func.lower()
    for prefix, db_name in _TABLE_PREFIX_TO_DB.items():
        if prefix in caller_func_lower:
            return db_name

    if _is_discovery_mode():
        logger.warning(
            "compatibility_adapter (discovery mode): unknown caller '%s' in '%s', "
            "falling back to orchestration.db.",
            caller_func,
            caller_file,
        )
        return "orchestration"

    raise RuntimeError(
        f"compatibility_adapter: unknown caller '{caller_func}' in '{caller_file}'. "
        "production fail-close (entity ownership 違反防止)。"
    )


def _db_path_for(db_name: str) -> str:
    """Return the on-disk SQLite path for a canonical db name."""
    filename = _DB_NAME_TO_FILENAME[_validate_db_name(db_name)]
    return str(_resolve_helix_dir() / filename)


def _open_sqlite_connection(
    db_path: str | Path | None, ensure_schema: bool
) -> Connection:
    target_path = helix_db._resolve_db_path(db_path)
    helix_db._prepare_db_path(target_path)
    conn = helix_db._connect(target_path)
    if ensure_schema:
        helix_db._ensure_schema(conn)
    return conn


def _open_cutover_connection(
    db_name: str, ensure_schema: bool
) -> Iterator[Connection]:
    """Open the routed DB using the legacy schema bootstrap as a Phase 4.A.1 shim."""
    db_path = _db_path_for(db_name)
    return helix_db._write_connection(db_path, ensure_schema=ensure_schema)


@contextmanager
def _open_dual_write_connection(
    target_db: str, ensure_schema: bool
) -> Iterator[_DualWriteConnection]:
    legacy_path = helix_db._resolve_db_path(None)
    target_path = _db_path_for(target_db)
    with helix_db.file_lock(helix_db.HELIX_DB_LOCK_NAME):
        legacy_conn: Connection | None = None
        new_conn: Connection | None = None
        try:
            legacy_conn = _open_sqlite_connection(legacy_path, ensure_schema)
            new_conn = _open_sqlite_connection(target_path, ensure_schema)
            dual_conn = _DualWriteConnection(legacy_conn=legacy_conn, new_conn=new_conn)
            yield dual_conn
            dual_conn.commit()
        except Exception:
            if legacy_conn is not None and new_conn is not None:
                dual_conn.rollback()
            raise
        finally:
            if legacy_conn is not None and new_conn is not None:
                dual_conn.close()
            else:
                for conn in (legacy_conn, new_conn):
                    if conn is None:
                        continue
                    conn.close()


# @helix:index id=compatibility-adapter.write-connection domain=cli/lib summary=旧 _write_connection の 6 db routing 互換 API
@contextmanager
def write_connection(
    db_path: str | Path | None = None, ensure_schema: bool = True
) -> Iterator[Connection | _DualWriteConnection]:
    """Compatibility wrapper for ``helix_db._write_connection``.

    Behavior:
    - ``db_path is not None``: delegate to the legacy implementation unchanged.
    - ``db_path is None`` and ``HELIX_DB_CUTOVER=1``: route to the planned split
      database path.
    - ``db_path is None`` and cutover is disabled: dual-write to legacy
      ``helix.db`` and the routed split db.
    """
    if db_path is not None:
        with helix_db._write_connection(db_path, ensure_schema=ensure_schema) as conn:
            yield conn
        return

    caller_file, caller_func = _discover_caller()
    target_db = _route_to_db(caller_file, caller_func)
    if _is_cutover_enabled():
        logger.debug(
            "compatibility_adapter: cutover enabled, routing writes to %s.db only.",
            target_db,
        )
        with _open_cutover_connection(target_db, ensure_schema) as conn:
            yield conn
        return

    logger.debug(
        "compatibility_adapter: dual-write enabled for legacy helix.db and %s.db.",
        target_db,
    )
    with _open_dual_write_connection(target_db, ensure_schema) as conn:
        yield conn


# @helix:index id=compatibility-adapter.read-cross-db-projection domain=cli/lib summary=projection_state の cross-db read helper
def read_cross_db_projection(projector_id: str, db_name: str) -> dict[str, Any] | None:
    """Read a projection snapshot through the approved helper boundary."""
    if not projector_id:
        raise ValueError("projector_id must not be empty")
    if projector_id not in _KNOWN_PROJECTORS:
        raise ValueError(
            f"unknown projector_id '{projector_id}'. known: {sorted(_KNOWN_PROJECTORS)}"
        )
    _validate_db_name(db_name)
    db_path = Path(_db_path_for(db_name))
    if not db_path.exists():
        logger.warning(
            "compatibility_adapter: projection db is missing for projector_id=%s db_name=%s path=%s",
            projector_id,
            db_name,
            db_path,
        )
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT snapshot
            FROM projection_state
            WHERE projector_id = ? AND db_name = ?
            """,
            (projector_id, db_name),
        ).fetchone()
    finally:
        conn.close()

    if row is None or row["snapshot"] is None:
        return None
    return json.loads(row["snapshot"])
