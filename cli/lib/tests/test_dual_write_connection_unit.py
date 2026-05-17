"""Unit tests for cli/lib/dual_write_connection.py.

設計参照:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md §A
- docs/v2/L4-test-design/PLAN-084-unit-test-design.md §2 (U-ADAPTER-006〜010 補助)
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from cli.lib.dual_write_connection import _DualWriteConnection


class _FakeCursor:
    def __init__(self, lastrowid: int | None = None):
        self.lastrowid = lastrowid


class _RecordingConnection:
    def __init__(self) -> None:
        self.execute_calls = 0
        self.executemany_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def execute(self, sql: str, params: Any = ()) -> _FakeCursor:
        self.execute_calls += 1
        return _FakeCursor(lastrowid=self.execute_calls)

    def executemany(self, sql: str, params_list: Any) -> _FakeCursor:
        self.executemany_calls += 1
        return _FakeCursor(lastrowid=len(list(params_list)))

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


class _BusyThenSuccessConnection(_RecordingConnection):
    def __init__(self, busy_count: int) -> None:
        super().__init__()
        self._busy_count = busy_count

    def execute(self, sql: str, params: Any = ()) -> _FakeCursor:
        self.execute_calls += 1
        if self.execute_calls <= self._busy_count:
            raise sqlite3.OperationalError("database is locked")
        return _FakeCursor(lastrowid=99)


class _FailingCommitConnection(_RecordingConnection):
    def commit(self) -> None:
        self.commit_calls += 1
        raise sqlite3.OperationalError("new commit failed")


class _FailingExecuteConnection(_RecordingConnection):
    def execute(self, sql: str, params: Any = ()) -> _FakeCursor:
        self.execute_calls += 1
        raise sqlite3.OperationalError("new execute failed")


# @helix:index id=plan084.dual-write.unit domain=cli/lib/tests summary=PLAN-084 dual_write_connection retry and error policy unit tests
class TestDualWriteConnection:
    def test_retries_sqlite_busy_up_to_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-006 補助 (SQLITE_BUSY は retry 後に成功する)"""
        sleep_calls: list[float] = []
        legacy = _BusyThenSuccessConnection(busy_count=2)
        new = _RecordingConnection()
        conn = _DualWriteConnection(legacy, new)
        monkeypatch.setattr("cli.lib.dual_write_connection.time.sleep", sleep_calls.append)

        cursor = conn.execute("INSERT INTO sample(value) VALUES (?)", ("ok",))

        assert cursor.lastrowid == 99
        assert conn.lastrowid == 99
        assert legacy.execute_calls == 3
        assert new.execute_calls == 1
        assert sleep_calls == [0.1, 0.1]

    def test_new_execute_failure_warns_without_raising(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-007 補助 (new 側 execute failure は WARN のみ)"""
        legacy = _RecordingConnection()
        new = _FailingExecuteConnection()
        conn = _DualWriteConnection(legacy, new)
        caplog.set_level("WARNING", logger="cli.lib.dual_write_connection")

        cursor = conn.execute("INSERT INTO sample(value) VALUES (?)", ("ok",))

        assert cursor.lastrowid == 1
        assert legacy.execute_calls == 1
        assert new.execute_calls == 1
        assert new.rollback_calls == 1
        assert any("new db execute failed" in record.getMessage() for record in caplog.records)

    def test_new_commit_failure_warns_and_rolls_back_new(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-007 補助 (new 側 commit failure は WARN + rollback)"""
        legacy = _RecordingConnection()
        new = _FailingCommitConnection()
        conn = _DualWriteConnection(legacy, new)
        caplog.set_level("WARNING", logger="cli.lib.dual_write_connection")

        conn.commit()

        assert legacy.commit_calls == 1
        assert new.commit_calls == 1
        assert new.rollback_calls == 1
        assert any("new db commit failed" in record.getMessage() for record in caplog.records)

    def test_rollback_attempts_both_connections_even_when_legacy_fails(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-008 補助 (rollback は両 DB を試行する)"""

        class _LegacyRollbackFailure(_RecordingConnection):
            def rollback(self) -> None:
                self.rollback_calls += 1
                raise sqlite3.OperationalError("legacy rollback failed")

        legacy = _LegacyRollbackFailure()
        new = _RecordingConnection()
        conn = _DualWriteConnection(legacy, new)

        with pytest.raises(sqlite3.OperationalError, match="legacy rollback failed"):
            conn.rollback()

        assert legacy.rollback_calls == 1
        assert new.rollback_calls == 1

    def test_close_attempts_both_connections(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-009 補助 (close は両 DB を閉じる)"""
        legacy = _RecordingConnection()
        new = _RecordingConnection()
        conn = _DualWriteConnection(legacy, new)

        conn.close()

        assert legacy.close_calls == 1
        assert new.close_calls == 1
