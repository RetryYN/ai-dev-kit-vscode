"""Compatibility adapter for phased helix.db separation.

Phase 4.A.1 scope:
- Keep the old ``helix_db._write_connection`` signature compatible.
- Route ``db_path=None`` calls to one of the planned 6 databases.
- Use the legacy single-db path until dual-write lands in Sprint 4.A.2.

Design references:
- D-API-SEP-draft §2/§4
- D-DB-SEP-draft §5/§6
"""

from contextlib import contextmanager
from pathlib import Path
from sqlite3 import Connection
from typing import Any, Iterator
import inspect
import logging
import os

from . import helix_db

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


def _open_cutover_connection(
    db_name: str, ensure_schema: bool
) -> Iterator[Connection]:
    """Open the routed DB using the legacy schema bootstrap as a Phase 4.A.1 shim."""
    db_path = _db_path_for(db_name)
    return helix_db._write_connection(db_path, ensure_schema=ensure_schema)


def _legacy_only_connection(ensure_schema: bool) -> Iterator[Connection]:
    """Phase 4.A.1 fallback while dual-write is deferred to Sprint 4.A.2."""
    logger.debug(
        "compatibility_adapter: dual-write not enabled yet, using legacy helix.db only."
    )
    return helix_db._write_connection(None, ensure_schema=ensure_schema)


def _resolve_connection_factory(
    target_db: str, ensure_schema: bool
) -> Iterator[Connection]:
    if _is_cutover_enabled():
        logger.debug(
            "compatibility_adapter: cutover enabled, routing writes to %s.db only.",
            target_db,
        )
        return _open_cutover_connection(target_db, ensure_schema)
    return _legacy_only_connection(ensure_schema)


# @helix:index id=compatibility-adapter.write-connection domain=cli/lib summary=旧 _write_connection の 6 db routing 互換 API
@contextmanager
def write_connection(
    db_path: str | Path | None = None, ensure_schema: bool = True
) -> Iterator[Connection]:
    """Compatibility wrapper for ``helix_db._write_connection``.

    Behavior:
    - ``db_path is not None``: delegate to the legacy implementation unchanged.
    - ``db_path is None`` and ``HELIX_DB_CUTOVER=1``: route to the planned split
      database path.
    - ``db_path is None`` and cutover is disabled: stay on legacy ``helix.db``.

    Phase 4.A.1 intentionally does not dual-write. That bridge is a Sprint
    4.A.2 carry item to avoid changing runtime semantics in the initial
    skeleton.
    """
    if db_path is not None:
        with helix_db._write_connection(db_path, ensure_schema=ensure_schema) as conn:
            yield conn
        return

    caller_file, caller_func = _discover_caller()
    target_db = _route_to_db(caller_file, caller_func)
    connection_factory = _resolve_connection_factory(target_db, ensure_schema)
    with connection_factory as conn:
        yield conn


# @helix:index id=compatibility-adapter.read-cross-db-projection domain=cli/lib summary=projection_state の cross-db read helper skeleton
def read_cross_db_projection(projector_id: str, db_name: str) -> dict[str, Any] | None:
    """Read a projection snapshot through the approved helper boundary.

    Phase 4.A.1 keeps this helper as a skeleton so application code has a
    stable import target before the real cross-db snapshot path lands in Sprint
    4.A.2. The final implementation will use a direct sqlite connection to the
    target db and must not rely on ATTACH from the application layer.
    """
    if not projector_id:
        raise ValueError("projector_id must not be empty")
    _validate_db_name(db_name)
    logger.debug(
        "compatibility_adapter: read_cross_db_projection(%s, %s) is a Phase 4.A.1 skeleton.",
        projector_id,
        db_name,
    )
    return None
