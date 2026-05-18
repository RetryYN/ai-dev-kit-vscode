import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _session_telemetry_index_names(conn: sqlite3.Connection) -> list[str]:
    return sorted(
        row["name"]
        for row in conn.execute("PRAGMA index_list(session_telemetry)").fetchall()
    )


@pytest.fixture
def v26_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / ".helix" / "test_v27.db"
    helix_db.init_db(str(db_path))
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    helix_db._migrate_v23_to_v24(conn)
    helix_db._migrate_v24_to_v25(conn)
    helix_db._migrate_v25_to_v26(conn)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def v27_db(v26_db: sqlite3.Connection) -> sqlite3.Connection:
    helix_db._migrate_v26_to_v27(v26_db)
    return v26_db


def test_v26_to_v27_migrate_succeeds(v26_db: sqlite3.Connection) -> None:
    helix_db._migrate_v26_to_v27(v26_db)

    table = v26_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'session_telemetry'"
    ).fetchone()
    columns = {
        row["name"]
        for row in v26_db.execute("PRAGMA table_info(session_telemetry)").fetchall()
    }

    assert table is not None
    assert {
        "id",
        "session_id",
        "started_at",
        "ended_at",
        "actor",
        "related_plan_id",
        "tool_uses_count",
        "tokens_total",
        "cost_usd",
        "last_updated_at",
    } <= columns
    assert _session_telemetry_index_names(v26_db) == [
        "idx_session_telemetry_actor",
        "idx_session_telemetry_related_plan",
        "idx_session_telemetry_started_at",
        "sqlite_autoindex_session_telemetry_1",
    ]


def test_v27_migrate_is_idempotent(v26_db: sqlite3.Connection) -> None:
    helix_db._migrate_v26_to_v27(v26_db)
    first_indexes = _session_telemetry_index_names(v26_db)

    helix_db._migrate_v26_to_v27(v26_db)

    tables = v26_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'session_telemetry'"
    ).fetchall()

    assert len(tables) == 1
    assert _session_telemetry_index_names(v26_db) == first_indexes


def test_v27_session_id_unique(v27_db: sqlite3.Connection) -> None:
    v27_db.execute(
        """
        INSERT INTO session_telemetry (session_id, actor)
        VALUES (?, ?)
        """,
        ("sess-001", "opus"),
    )

    with pytest.raises(sqlite3.IntegrityError):
        v27_db.execute(
            """
            INSERT INTO session_telemetry (session_id, actor)
            VALUES (?, ?)
            """,
            ("sess-001", "opus"),
        )


def test_v27_session_id_not_null(v27_db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        v27_db.execute(
            """
            INSERT INTO session_telemetry (session_id, actor)
            VALUES (?, ?)
            """,
            (None, "opus"),
        )


def test_v27_default_counts_are_zero(v27_db: sqlite3.Connection) -> None:
    v27_db.execute(
        """
        INSERT INTO session_telemetry (session_id, actor)
        VALUES (?, ?)
        """,
        ("sess-defaults", "codex"),
    )
    row = v27_db.execute(
        """
        SELECT tool_uses_count, tokens_total, cost_usd
        FROM session_telemetry
        WHERE session_id = ?
        """,
        ("sess-defaults",),
    ).fetchone()

    assert row is not None
    assert row["tool_uses_count"] == 0
    assert row["tokens_total"] == 0
    assert row["cost_usd"] == pytest.approx(0.0)


def test_v27_upsert_inserts_new(v27_db: sqlite3.Connection) -> None:
    rowid = helix_db._upsert_row(
        v27_db,
        "session_telemetry",
        {
            "session_id": "sess-insert",
            "actor": "opus",
            "tool_uses_count": 1,
            "tokens_total": 200,
            "cost_usd": 0.01,
        },
        conflict_column="session_id",
    )
    row = v27_db.execute(
        "SELECT rowid AS row_id, actor, tokens_total FROM session_telemetry WHERE session_id = ?",
        ("sess-insert",),
    ).fetchone()

    assert row is not None
    assert rowid == row["row_id"]
    assert row["actor"] == "opus"
    assert row["tokens_total"] == 200


def test_v27_upsert_updates_existing(v27_db: sqlite3.Connection) -> None:
    rowid1 = helix_db._upsert_row(
        v27_db,
        "session_telemetry",
        {
            "session_id": "sess-001",
            "actor": "opus",
            "tool_uses_count": 5,
            "tokens_total": 1000,
            "cost_usd": 0.05,
        },
        conflict_column="session_id",
    )

    rowid2 = helix_db._upsert_row(
        v27_db,
        "session_telemetry",
        {
            "session_id": "sess-001",
            "actor": "opus",
            "tool_uses_count": 10,
            "tokens_total": 2500,
            "cost_usd": 0.12,
        },
        conflict_column="session_id",
    )

    row = v27_db.execute(
        """
        SELECT tool_uses_count, tokens_total, cost_usd
        FROM session_telemetry
        WHERE session_id = ?
        """,
        ("sess-001",),
    ).fetchone()
    count = v27_db.execute(
        "SELECT COUNT(*) AS c FROM session_telemetry"
    ).fetchone()

    assert rowid1 == rowid2
    assert row is not None
    assert row["tool_uses_count"] == 10
    assert row["tokens_total"] == 2500
    assert abs(row["cost_usd"] - 0.12) < 1e-9
    assert count is not None
    assert count["c"] == 1


def test_v27_related_plan_id_nullable(v27_db: sqlite3.Connection) -> None:
    v27_db.execute(
        """
        INSERT INTO session_telemetry (session_id, actor, related_plan_id)
        VALUES (?, ?, ?)
        """,
        ("sess-null-plan", "codex", None),
    )
    row = v27_db.execute(
        "SELECT related_plan_id FROM session_telemetry WHERE session_id = ?",
        ("sess-null-plan",),
    ).fetchone()

    assert row is not None
    assert row["related_plan_id"] is None


def test_v27_cost_usd_accepts_float(v27_db: sqlite3.Connection) -> None:
    v27_db.execute(
        """
        INSERT INTO session_telemetry (session_id, actor, cost_usd)
        VALUES (?, ?, ?)
        """,
        ("sess-float", "codex", 1.234),
    )
    row = v27_db.execute(
        "SELECT cost_usd FROM session_telemetry WHERE session_id = ?",
        ("sess-float",),
    ).fetchone()

    assert row is not None
    assert row["cost_usd"] == pytest.approx(1.234)


def test_v27_indexes_created(v27_db: sqlite3.Connection) -> None:
    indexes = _session_telemetry_index_names(v27_db)

    assert "idx_session_telemetry_actor" in indexes
    assert "idx_session_telemetry_started_at" in indexes
    assert "idx_session_telemetry_related_plan" in indexes


def test_init_db_to_v27_sequential(tmp_path: Path) -> None:
    db_path = tmp_path / "sequential.db"
    helix_db.init_db(str(db_path))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        versions = [
            row["version"]
            for row in conn.execute(
                "SELECT version FROM schema_version ORDER BY version"
            ).fetchall()
        ]
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        triggers = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert max(versions) == helix_db.CURRENT_SCHEMA_VERSION
    assert helix_db.CURRENT_SCHEMA_VERSION >= 32
    assert {24, 25, 26, 27}.issubset(set(versions))
    assert "design_sprint_drive_decisions" in tables
    assert "automation_runs" in tables
    assert "audit_log" in tables
    assert "session_telemetry" in tables
    assert {
        "automation_runs_no_delete",
        "automation_runs_terminal_final",
        "automation_runs_id_immutable",
        "automation_runs_run_kind_immutable",
        "automation_runs_started_at_immutable",
        "audit_log_no_delete",
        "audit_log_payload_immutable",
    }.issubset(triggers)


def test_migrate_v23_db_to_v27(tmp_path: Path) -> None:
    db_path = tmp_path / "v23_to_v27.db"
    helix_db.init_db(str(db_path))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("DELETE FROM schema_version WHERE version >= 24")
        conn.commit()

        helix_db.migrate(conn)

        versions = [
            row["version"]
            for row in conn.execute(
                "SELECT version FROM schema_version ORDER BY version"
            ).fetchall()
        ]
    finally:
        conn.close()

    assert max(versions) == helix_db.CURRENT_SCHEMA_VERSION
    assert helix_db.CURRENT_SCHEMA_VERSION >= 32
    for version in range(18, 28):
        assert version in versions, f"version {version} missing in schema_version"
