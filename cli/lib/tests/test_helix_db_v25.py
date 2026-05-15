import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _automation_index_names(conn: sqlite3.Connection) -> list[str]:
    return sorted(
        row["name"]
        for row in conn.execute("PRAGMA index_list(automation_runs)").fetchall()
    )


def _automation_trigger_names(conn: sqlite3.Connection) -> list[str]:
    return sorted(
        row["name"]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'trigger' AND tbl_name = 'automation_runs'
            ORDER BY name
            """
        ).fetchall()
    )


@pytest.fixture
def v24_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / ".helix" / "test_v25.db"
    helix_db.init_db(str(db_path))
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    helix_db._migrate_v23_to_v24(conn)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def v25_db(v24_db: sqlite3.Connection) -> sqlite3.Connection:
    helix_db._migrate_v24_to_v25(v24_db)
    return v24_db


def test_v24_to_v25_migrate_succeeds(v24_db: sqlite3.Connection) -> None:
    helix_db._migrate_v24_to_v25(v24_db)

    table = v24_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'automation_runs'"
    ).fetchone()
    columns = {
        row["name"] for row in v24_db.execute("PRAGMA table_info(automation_runs)").fetchall()
    }

    assert table is not None
    assert {
        "id",
        "run_kind",
        "plan_id",
        "trigger_actor",
        "started_at",
        "ended_at",
        "status",
        "exit_code",
        "summary",
        "retry_count",
        "max_retries",
        "last_error",
    } <= columns
    assert _automation_index_names(v24_db) == [
        "idx_automation_runs_kind",
        "idx_automation_runs_started_at",
        "idx_automation_runs_status",
    ]
    assert _automation_trigger_names(v24_db) == [
        "automation_runs_id_immutable",
        "automation_runs_no_delete",
        "automation_runs_run_kind_immutable",
        "automation_runs_started_at_immutable",
        "automation_runs_terminal_final",
    ]


def test_v25_migrate_is_idempotent(v24_db: sqlite3.Connection) -> None:
    helix_db._migrate_v24_to_v25(v24_db)
    first_trigger_names = _automation_trigger_names(v24_db)

    helix_db._migrate_v24_to_v25(v24_db)

    tables = v24_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'automation_runs'"
    ).fetchall()

    assert len(tables) == 1
    assert _automation_index_names(v24_db) == [
        "idx_automation_runs_kind",
        "idx_automation_runs_started_at",
        "idx_automation_runs_status",
    ]
    assert _automation_trigger_names(v24_db) == first_trigger_names


def test_v25_status_enum_check(v25_db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        v25_db.execute(
            """
            INSERT INTO automation_runs (run_kind, trigger_actor, status)
            VALUES (?, ?, ?)
            """,
            ("gate", "test-actor", "unknown"),
        )


def test_v25_default_status_is_pending(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test-actor"),
    )
    row = v25_db.execute(
        "SELECT status FROM automation_runs WHERE id = ?",
        (int(cursor.lastrowid),),
    ).fetchone()

    assert row is not None
    assert row["status"] == "pending"


def test_v25_delete_rejected(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test-actor"),
    )

    with pytest.raises(sqlite3.IntegrityError, match="automation_runs is append-only"):
        v25_db.execute("DELETE FROM automation_runs WHERE id = ?", (int(cursor.lastrowid),))


def test_v25_id_immutable(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test-actor"),
    )

    with pytest.raises(sqlite3.IntegrityError, match=r"automation_runs\.id is immutable"):
        v25_db.execute(
            "UPDATE automation_runs SET id = ? WHERE id = ?",
            (999, int(cursor.lastrowid)),
        )


def test_v25_run_kind_immutable(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test-actor"),
    )

    with pytest.raises(sqlite3.IntegrityError, match=r"automation_runs\.run_kind is immutable"):
        v25_db.execute(
            "UPDATE automation_runs SET run_kind = ? WHERE id = ?",
            ("deploy", int(cursor.lastrowid)),
        )


def test_v25_started_at_immutable(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test-actor"),
    )

    with pytest.raises(sqlite3.IntegrityError, match=r"automation_runs\.started_at is immutable"):
        v25_db.execute(
            "UPDATE automation_runs SET started_at = ? WHERE id = ?",
            ("2026-05-16T00:00:00", int(cursor.lastrowid)),
        )


def test_v25_terminal_status_is_final(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        """
        INSERT INTO automation_runs (run_kind, trigger_actor, status, summary)
        VALUES (?, ?, ?, ?)
        """,
        ("gate", "test-actor", "completed", "done"),
    )

    with pytest.raises(sqlite3.IntegrityError, match="automation_runs terminal status is final"):
        v25_db.execute(
            "UPDATE automation_runs SET summary = ? WHERE id = ?",
            ("changed", int(cursor.lastrowid)),
        )


def test_v25_lifecycle_transition_via_helper(v25_db: sqlite3.Connection) -> None:
    cursor = v25_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test-actor"),
    )
    run_id = int(cursor.lastrowid)
    allowed = {
        "pending": ["running", "cancelled"],
        "running": ["completed", "failed", "cancelled"],
    }

    assert helix_db._transition_lifecycle_status(
        v25_db, "automation_runs", run_id, "pending", "running", allowed
    )
    assert helix_db._transition_lifecycle_status(
        v25_db, "automation_runs", run_id, "running", "completed", allowed
    )
    row = v25_db.execute(
        "SELECT status FROM automation_runs WHERE id = ?",
        (run_id,),
    ).fetchone()

    assert row is not None
    assert row["status"] == "completed"
    with pytest.raises(sqlite3.IntegrityError):
        helix_db._transition_lifecycle_status(
            v25_db, "automation_runs", run_id, "completed", "running", allowed
        )
