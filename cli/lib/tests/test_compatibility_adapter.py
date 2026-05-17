"""U-ADAPTER unit tests for cli/lib/compatibility_adapter.py.

設計参照:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md §2/§3/§4/§5/§6
- docs/v2/L4-test-design/PLAN-084-unit-test-design.md §2 (U-ADAPTER-001〜015)

DoD 検証: U-ADAPTER-001〜015
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from cli.lib import compatibility_adapter, helix_db
from cli.lib.dual_write_connection import _DualWriteConnection


# @helix:index id=plan084.u-adapter.tests domain=cli/lib/tests summary=PLAN-084 compatibility_adapter unit tests


def _open_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _assert_fixture_sqlite_ready(tmp_root: Path) -> None:
    smoke_db = tmp_root / "fixture_smoke.db"
    with _open_conn(smoke_db) as conn:
        row = conn.execute("SELECT value FROM fixture_smoke LIMIT 1").fetchone()
    assert row is not None
    assert row["value"] == "ready"


def _fetch_values(db_path: Path, table_name: str) -> list[str]:
    if not db_path.exists():
        return []
    with _open_conn(db_path) as conn:
        rows = conn.execute(f"SELECT value FROM {table_name} ORDER BY id").fetchall()
    return [str(row["value"]) for row in rows]


class _ProxyConnection:
    def __init__(self, inner: sqlite3.Connection):
        self._inner = inner
        self.insert_calls = 0

    def execute(self, sql: str, params: Any = ()) -> sqlite3.Cursor:
        if sql.lstrip().upper().startswith("INSERT"):
            self.insert_calls += 1
        return self._inner.execute(sql, params)

    def executemany(self, sql: str, params_list: Any) -> sqlite3.Cursor:
        params = list(params_list)
        if sql.lstrip().upper().startswith("INSERT"):
            self.insert_calls += len(params)
        return self._inner.executemany(sql, params)

    def commit(self) -> None:
        self._inner.commit()

    def rollback(self) -> None:
        self._inner.rollback()

    def close(self) -> None:
        self._inner.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _FailingExecuteConnection(_ProxyConnection):
    def __init__(self, inner: sqlite3.Connection, failure_message: str, table_name: str):
        super().__init__(inner)
        self._failure_message = failure_message
        self._table_name = table_name

    def execute(self, sql: str, params: Any = ()) -> sqlite3.Cursor:
        if sql.lstrip().upper().startswith("INSERT") and self._table_name in sql:
            raise sqlite3.OperationalError(self._failure_message)
        return super().execute(sql, params)


def _patch_agent_slots_caller(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        compatibility_adapter,
        "_discover_caller",
        lambda: ("agent_slots.py", "fire_slot"),
    )


@pytest.fixture
def sqlite_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """実 SQLite を使う一時ディレクトリを用意し、HELIX_DB_PATH を固定する。"""
    monkeypatch.setenv("HELIX_DB_PATH", str(tmp_path / "helix.db"))
    with sqlite3.connect(str(tmp_path / "fixture_smoke.db")) as conn:
        conn.execute("CREATE TABLE fixture_smoke (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO fixture_smoke(value) VALUES ('ready')")
    return tmp_path


# @helix:index id=plan084.u-adapter.route domain=cli/lib/tests summary=compatibility_adapter routing and read helper active cases
class TestCompatibilityAdapterRouting:
    def test_u_adapter_001_routes_agent_slots_to_orchestration(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-001 (agent_slots.py は orchestration.db に route する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        assert compatibility_adapter._route_to_db("agent_slots.py", "fire_slot") == "orchestration"

    def test_u_adapter_002_routes_scrum_local_to_scrum(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-002 (scrum_local.py は scrum.db に route する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        assert compatibility_adapter._route_to_db("scrum_local.py", "add_local_hypothesis") == "scrum"

    def test_u_adapter_003_routes_audit_to_backend(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-003 (audit.py は backend.db に route する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        assert compatibility_adapter._route_to_db("audit.py", "post_audit") == "backend"

    def test_u_adapter_004_routes_helix_push_to_backend(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-004 (helix-push は backend.db に route する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        assert compatibility_adapter._route_to_db("helix-push", "record_push") == "backend"

    def test_u_adapter_005_routes_helix_agent_to_orchestration(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-005 (helix-agent は orchestration.db に route する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        assert compatibility_adapter._route_to_db("helix-agent", "list_slots") == "orchestration"

    def test_u_adapter_013_returns_none_when_projection_db_is_missing(
        self, sqlite_tmp_root: Path
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-013 (db file 不在でも read helper は None を返す)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        assert compatibility_adapter.read_cross_db_projection("phase_state", "orchestration") is None

    @pytest.mark.parametrize("discovery_mode", [False, True], ids=["production", "discovery"])
    def test_u_adapter_014_unknown_caller_fail_close_or_fallback(
        self,
        sqlite_tmp_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        discovery_mode: bool,
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-014 (unknown caller は production fail-close / discovery fallback)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        if discovery_mode:
            monkeypatch.setenv("HELIX_DB_DISCOVERY", "1")
            caplog.set_level("WARNING", logger=compatibility_adapter.logger.name)
            assert compatibility_adapter._route_to_db("unknown_module.py", "unknown_func") == "orchestration"
            assert any(
                record.levelname == "WARNING" and "discovery mode" in record.getMessage()
                for record in caplog.records
            )
            return

        monkeypatch.delenv("HELIX_DB_DISCOVERY", raising=False)
        with pytest.raises(RuntimeError, match=r"production fail-close \(entity ownership 違反防止\)") as excinfo:
            compatibility_adapter._route_to_db("unknown_module.py", "unknown_func")
        assert "unknown caller 'unknown_func'" in str(excinfo.value)


# @helix:index id=plan084.u-adapter.write domain=cli/lib/tests summary=compatibility_adapter explicit db_path delegate active case
class TestCompatibilityAdapterWriteConnection:
    def test_u_adapter_006_dual_write_writes_to_legacy_and_target_db(
        self, sqlite_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-006 (dual-write 期間は legacy と新 db の両方へ write する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        _patch_agent_slots_caller(monkeypatch)
        table_name = "dual_write_active"

        with compatibility_adapter.write_connection() as conn:
            assert isinstance(conn, _DualWriteConnection)
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)"
            )
            cursor = conn.execute(
                f"INSERT INTO {table_name}(value) VALUES (?)",
                ("row-1",),
            )
            assert cursor.lastrowid == 1
            assert conn.lastrowid == 1

        assert _fetch_values(sqlite_tmp_root / "helix.db", table_name) == ["row-1"]
        assert _fetch_values(sqlite_tmp_root / "orchestration.db", table_name) == ["row-1"]

    def test_u_adapter_007_new_db_write_failure_only_warns(
        self,
        sqlite_tmp_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-007 (dual-write 期間の新 db write 失敗は WARN のみで継続する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        _patch_agent_slots_caller(monkeypatch)
        table_name = "dual_write_warn_only"
        original_open = compatibility_adapter._open_sqlite_connection
        new_db_path = sqlite_tmp_root / "orchestration.db"
        caplog.set_level("WARNING", logger="cli.lib.dual_write_connection")

        def _patched_open(db_path: str | Path | None, ensure_schema: bool) -> Any:
            conn = original_open(db_path, ensure_schema)
            if Path(str(db_path)) == new_db_path:
                return _FailingExecuteConnection(conn, "new insert failed", table_name)
            return conn

        monkeypatch.setattr(compatibility_adapter, "_open_sqlite_connection", _patched_open)

        with compatibility_adapter.write_connection() as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)"
            )
            cursor = conn.execute(
                f"INSERT INTO {table_name}(value) VALUES (?)",
                ("legacy-only",),
            )
            assert cursor.lastrowid == 1

        assert _fetch_values(sqlite_tmp_root / "helix.db", table_name) == ["legacy-only"]
        assert _fetch_values(new_db_path, table_name) == []
        assert any(
            "new db execute failed" in record.getMessage()
            for record in caplog.records
        )

    def test_u_adapter_008_legacy_write_failure_raises_critical_error(
        self, sqlite_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-008 (dual-write 期間の legacy write 失敗は critical raise する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        _patch_agent_slots_caller(monkeypatch)
        table_name = "dual_write_legacy_critical"
        original_open = compatibility_adapter._open_sqlite_connection
        legacy_db_path = sqlite_tmp_root / "helix.db"
        new_db_path = sqlite_tmp_root / "orchestration.db"
        tracking_new_conn: _ProxyConnection | None = None

        def _patched_open(db_path: str | Path | None, ensure_schema: bool) -> Any:
            nonlocal tracking_new_conn
            conn = original_open(db_path, ensure_schema)
            if Path(str(db_path)) == legacy_db_path:
                return _FailingExecuteConnection(conn, "legacy insert failed", table_name)
            if Path(str(db_path)) == new_db_path:
                tracking_new_conn = _ProxyConnection(conn)
                return tracking_new_conn
            return conn

        monkeypatch.setattr(compatibility_adapter, "_open_sqlite_connection", _patched_open)

        with pytest.raises(sqlite3.OperationalError, match="legacy insert failed"):
            with compatibility_adapter.write_connection() as conn:
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)"
                )
                conn.execute(
                    f"INSERT INTO {table_name}(value) VALUES (?)",
                    ("should-fail",),
                )

        assert _fetch_values(legacy_db_path, table_name) == []
        assert _fetch_values(new_db_path, table_name) == []
        assert tracking_new_conn is not None
        assert tracking_new_conn.insert_calls == 0

    def test_u_adapter_009_executemany_also_dual_writes(
        self, sqlite_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-009 (dual-write 期間の executemany も両経路へ write する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        _patch_agent_slots_caller(monkeypatch)
        table_name = "dual_write_many"

        with compatibility_adapter.write_connection() as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)"
            )
            conn.executemany(
                f"INSERT INTO {table_name}(value) VALUES (?)",
                [("row-1",), ("row-2",)],
            )

        assert _fetch_values(sqlite_tmp_root / "helix.db", table_name) == ["row-1", "row-2"]
        assert _fetch_values(sqlite_tmp_root / "orchestration.db", table_name) == ["row-1", "row-2"]

    def test_u_adapter_010_cutover_routes_only_to_split_db(
        self, sqlite_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-010 (cutover 後は 6 db のみへ write する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        _patch_agent_slots_caller(monkeypatch)
        monkeypatch.setenv("HELIX_DB_CUTOVER", "1")
        table_name = "cutover_only_target"

        with compatibility_adapter.write_connection() as conn:
            assert not isinstance(conn, _DualWriteConnection)
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)"
            )
            conn.execute(
                f"INSERT INTO {table_name}(value) VALUES (?)",
                ("new-only",),
            )

        assert _fetch_values(sqlite_tmp_root / "helix.db", table_name) == []
        assert _fetch_values(sqlite_tmp_root / "orchestration.db", table_name) == ["new-only"]

    def test_u_adapter_015_explicit_db_path_delegates_to_legacy_writer(
        self, sqlite_tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-015 (db_path 明示指定時は legacy helix_db._write_connection に委譲する)"""
        _assert_fixture_sqlite_ready(sqlite_tmp_root)
        db_path = sqlite_tmp_root / "explicit_delegate.db"
        original_write_connection = compatibility_adapter.helix_db._write_connection
        calls: list[tuple[str | Path | None, bool]] = []

        @contextmanager
        def _spy_write_connection(db_path_arg: str | Path | None, ensure_schema: bool = True):
            calls.append((db_path_arg, ensure_schema))
            with original_write_connection(db_path_arg, ensure_schema=ensure_schema) as conn:
                yield conn

        def _fail_route(*args: object, **kwargs: object) -> str:
            raise AssertionError("_route_to_db should not be called for explicit db_path")

        monkeypatch.setattr(compatibility_adapter.helix_db, "_write_connection", _spy_write_connection)
        monkeypatch.setattr(compatibility_adapter, "_route_to_db", _fail_route)

        with compatibility_adapter.write_connection(db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS explicit_delegate_smoke (id INTEGER PRIMARY KEY, value TEXT)"
            )
            conn.execute("INSERT INTO explicit_delegate_smoke(value) VALUES (?)", ("ok",))

        assert calls == [(db_path, True)]
        with _open_conn(db_path) as conn:
            row = conn.execute("SELECT value FROM explicit_delegate_smoke LIMIT 1").fetchone()
        assert row is not None
        assert row["value"] == "ok"


# @helix:index id=plan084.u-adapter.carry domain=cli/lib/tests summary=Phase 4.B carry placeholders for projector cases
class TestCompatibilityAdapterPhase4BCarry:
    @pytest.mark.skip(reason="HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-06-30")
    def test_u_adapter_011_reads_projection_state_after_cutover(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-011 (cutover 後の read helper は projection_state snapshot を返す)"""
        pass

    @pytest.mark.skip(reason="HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-06-30")
    def test_u_adapter_012_warns_when_projector_lag_exceeds_threshold(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-012 (projector lag が閾値超過したら WARN を出す)"""
        pass
