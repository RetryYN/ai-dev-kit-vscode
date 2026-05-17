"""Dual-write SQLite connection wrapper for PLAN-084 compatibility adapter.

Design references:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md §A
- cli/lib/compatibility_adapter.py
"""

from __future__ import annotations

import logging
import sqlite3
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

_MAX_BUSY_RETRIES = 5
_BUSY_BACKOFF_SECONDS = 0.1
_T = TypeVar("_T")


def _is_sqlite_busy(exc: sqlite3.Error) -> bool:
    sqlite_errorcode = getattr(exc, "sqlite_errorcode", None)
    sqlite_errorname = getattr(exc, "sqlite_errorname", "")
    message = str(exc).lower()
    return (
        sqlite_errorcode == sqlite3.SQLITE_BUSY
        or sqlite_errorname == "SQLITE_BUSY"
        or "database is locked" in message
        or "database is busy" in message
    )


def _call_with_busy_retry(operation_name: str, callback: Callable[[], _T]) -> _T:
    last_error: sqlite3.Error | None = None
    for attempt in range(1, _MAX_BUSY_RETRIES + 1):
        try:
            return callback()
        except sqlite3.Error as exc:
            if not _is_sqlite_busy(exc):
                raise
            last_error = exc
            if attempt == _MAX_BUSY_RETRIES:
                break
            logger.warning(
                "_DualWriteConnection: %s hit SQLITE_BUSY (attempt %d/%d); retrying in %.0fms.",
                operation_name,
                attempt,
                _MAX_BUSY_RETRIES,
                _BUSY_BACKOFF_SECONDS * 1000,
            )
            time.sleep(_BUSY_BACKOFF_SECONDS)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"_DualWriteConnection: retry loop for {operation_name} exited unexpectedly")


# @helix:index id=dual-write-connection.wrapper domain=cli/lib summary=PLAN-084 dual-write legacy/new sqlite synchronized wrapper
class _DualWriteConnection:
    """legacy + new db を atomic 2 phase commit で扱う synchronized wrapper."""

    def __init__(self, legacy_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
        self._legacy_conn = legacy_conn
        self._new_conn = new_conn
        self._lastrowid: int | None = None

    def execute(self, sql: str, params: Any = ()) -> sqlite3.Cursor:
        """Write to legacy first and treat new-db failure as warning-only."""
        legacy_cursor = _call_with_busy_retry(
            "legacy execute",
            lambda: self._legacy_conn.execute(sql, params),
        )
        self._lastrowid = getattr(legacy_cursor, "lastrowid", None)
        try:
            _call_with_busy_retry(
                "new execute",
                lambda: self._new_conn.execute(sql, params),
            )
        except sqlite3.Error as exc:
            if _is_sqlite_busy(exc):
                raise
            self._warn_new_db_failure("execute", exc)
            self._rollback_new_after_warning()
        return legacy_cursor

    def executemany(self, sql: str, params_list: Any) -> sqlite3.Cursor:
        """Apply batched writes to both DBs with the same error policy as execute()."""
        legacy_params = list(params_list)
        new_params = list(legacy_params)
        legacy_cursor = _call_with_busy_retry(
            "legacy executemany",
            lambda: self._legacy_conn.executemany(sql, legacy_params),
        )
        self._lastrowid = getattr(legacy_cursor, "lastrowid", None)
        try:
            _call_with_busy_retry(
                "new executemany",
                lambda: self._new_conn.executemany(sql, new_params),
            )
        except sqlite3.Error as exc:
            if _is_sqlite_busy(exc):
                raise
            self._warn_new_db_failure("executemany", exc)
            self._rollback_new_after_warning()
        return legacy_cursor

    def commit(self) -> None:
        """Commit legacy -> new; new-only failure is warning, legacy failure raises."""
        try:
            _call_with_busy_retry("legacy commit", self._legacy_conn.commit)
        except sqlite3.Error:
            self._rollback_both_best_effort()
            raise

        try:
            _call_with_busy_retry("new commit", self._new_conn.commit)
        except sqlite3.Error as exc:
            if _is_sqlite_busy(exc):
                self._rollback_new_after_warning()
                raise
            self._warn_new_db_failure("commit", exc)
            self._rollback_new_after_warning()

    def rollback(self) -> None:
        """Attempt rollback on both DBs even if the first rollback fails."""
        first_error: sqlite3.Error | None = None
        for operation_name, conn in (
            ("legacy rollback", self._legacy_conn),
            ("new rollback", self._new_conn),
        ):
            try:
                _call_with_busy_retry(operation_name, conn.rollback)
            except sqlite3.Error as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error

    def close(self) -> None:
        """Close both SQLite connections and surface the first close error."""
        first_error: sqlite3.Error | None = None
        for conn in (self._legacy_conn, self._new_conn):
            try:
                conn.close()
            except sqlite3.Error as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error

    @property
    def lastrowid(self) -> int | None:
        """Return the legacy connection lastrowid during the dual-write window."""
        return self._lastrowid

    def _warn_new_db_failure(self, operation_name: str, exc: sqlite3.Error) -> None:
        logger.warning(
            "_DualWriteConnection: new db %s failed; continuing with legacy result: %s",
            operation_name,
            exc,
        )

    def _rollback_new_after_warning(self) -> None:
        try:
            _call_with_busy_retry("new rollback", self._new_conn.rollback)
        except sqlite3.Error as exc:
            if _is_sqlite_busy(exc):
                raise
            logger.warning(
                "_DualWriteConnection: new db rollback after warning failed: %s",
                exc,
            )

    def _rollback_both_best_effort(self) -> None:
        for operation_name, conn in (
            ("legacy rollback", self._legacy_conn),
            ("new rollback", self._new_conn),
        ):
            try:
                _call_with_busy_retry(operation_name, conn.rollback)
            except sqlite3.Error as exc:
                logger.warning(
                    "_DualWriteConnection: %s during commit recovery failed: %s",
                    operation_name,
                    exc,
                )


__all__ = ["_DualWriteConnection"]
