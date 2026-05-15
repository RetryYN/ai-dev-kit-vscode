import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _audit_index_names(conn: sqlite3.Connection) -> list[str]:
    return sorted(row["name"] for row in conn.execute("PRAGMA index_list(audit_log)").fetchall())


def _audit_trigger_names(conn: sqlite3.Connection) -> list[str]:
    return sorted(
        row["name"]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'trigger' AND tbl_name = 'audit_log'
            ORDER BY name
            """
        ).fetchall()
    )


def _insert_audit_log(
    conn: sqlite3.Connection,
    *,
    audit_kind: str = "summary",
    actor: str = "tester",
    payload: str = '{"ok":true}',
    run_id: int | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO audit_log (audit_kind, actor, run_id, payload)
        VALUES (?, ?, ?, ?)
        """,
        (audit_kind, actor, run_id, payload),
    )
    return int(cursor.lastrowid)


@pytest.fixture
def v25_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / ".helix" / "test_v26.db"
    helix_db.init_db(str(db_path))
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    helix_db._migrate_v23_to_v24(conn)
    helix_db._migrate_v24_to_v25(conn)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def v26_db(v25_db: sqlite3.Connection) -> sqlite3.Connection:
    helix_db._migrate_v25_to_v26(v25_db)
    return v25_db


@pytest.fixture
def v26_db_with_run(v26_db: sqlite3.Connection) -> tuple[sqlite3.Connection, int]:
    cursor = v26_db.execute(
        "INSERT INTO automation_runs (run_kind, trigger_actor) VALUES (?, ?)",
        ("gate", "test"),
    )
    v26_db.commit()
    return v26_db, int(cursor.lastrowid)


def test_v25_to_v26_migrate_succeeds(v25_db: sqlite3.Connection) -> None:
    helix_db._migrate_v25_to_v26(v25_db)

    table = v25_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'audit_log'"
    ).fetchone()
    columns = {
        row["name"] for row in v25_db.execute("PRAGMA table_info(audit_log)").fetchall()
    }

    assert table is not None
    assert {"id", "audit_kind", "actor", "run_id", "payload", "recorded_at"} <= columns
    assert _audit_index_names(v25_db) == [
        "idx_audit_log_actor",
        "idx_audit_log_kind",
        "idx_audit_log_recorded_at",
        "idx_audit_log_run_id",
    ]
    assert _audit_trigger_names(v25_db) == [
        "audit_log_no_delete",
        "audit_log_payload_immutable",
    ]


def test_v26_migrate_is_idempotent(v25_db: sqlite3.Connection) -> None:
    helix_db._migrate_v25_to_v26(v25_db)
    first_trigger_names = _audit_trigger_names(v25_db)

    helix_db._migrate_v25_to_v26(v25_db)

    tables = v25_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'audit_log'"
    ).fetchall()

    assert len(tables) == 1
    assert _audit_index_names(v25_db) == [
        "idx_audit_log_actor",
        "idx_audit_log_kind",
        "idx_audit_log_recorded_at",
        "idx_audit_log_run_id",
    ]
    assert _audit_trigger_names(v25_db) == first_trigger_names


def test_v26_payload_immutable(v26_db: sqlite3.Connection) -> None:
    row_id = _insert_audit_log(v26_db)

    with pytest.raises(sqlite3.IntegrityError, match=r"audit_log\.payload is immutable"):
        v26_db.execute(
            "UPDATE audit_log SET payload = ? WHERE id = ?",
            ('{"ok":false}', row_id),
        )


def test_v26_delete_rejected(v26_db: sqlite3.Connection) -> None:
    row_id = _insert_audit_log(v26_db)

    with pytest.raises(sqlite3.IntegrityError, match="audit_log is append-only"):
        v26_db.execute("DELETE FROM audit_log WHERE id = ?", (row_id,))


def test_v26_payload_not_null(v26_db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        v26_db.execute(
            """
            INSERT INTO audit_log (audit_kind, actor, payload)
            VALUES (?, ?, ?)
            """,
            ("summary", "tester", None),
        )


def test_v26_run_id_fk(v26_db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        v26_db.execute(
            """
            INSERT INTO audit_log (audit_kind, actor, run_id, payload)
            VALUES (?, ?, ?, ?)
            """,
            ("summary", "tester", 999, '{"ok":true}'),
        )


def test_v26_run_id_nullable(v26_db: sqlite3.Connection) -> None:
    row_id = _insert_audit_log(v26_db, run_id=None)
    row = v26_db.execute("SELECT run_id FROM audit_log WHERE id = ?", (row_id,)).fetchone()

    assert row is not None
    assert row["run_id"] is None


def test_v26_other_columns_updatable(v26_db_with_run: tuple[sqlite3.Connection, int]) -> None:
    conn, run_id = v26_db_with_run
    row_id = _insert_audit_log(conn, audit_kind="summary", actor="before", run_id=run_id)

    conn.execute(
        "UPDATE audit_log SET audit_kind = ?, actor = ? WHERE id = ?",
        ("qa_check", "after", row_id),
    )
    row = conn.execute(
        "SELECT audit_kind, actor, payload FROM audit_log WHERE id = ?",
        (row_id,),
    ).fetchone()

    assert row is not None
    assert row["audit_kind"] == "qa_check"
    assert row["actor"] == "after"
    assert row["payload"] == '{"ok":true}'
