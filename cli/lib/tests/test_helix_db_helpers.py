import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


@pytest.fixture
def fresh_conn(tmp_path: Path):
    connections: list[sqlite3.Connection] = []

    def _create(name: str = "helpers.db") -> sqlite3.Connection:
        db_path = tmp_path / name
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        connections.append(conn)
        return conn

    yield _create

    for conn in connections:
        conn.close()


def _create_upsert_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE session_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            tokens_used INTEGER,
            model TEXT,
            note TEXT
        )
        """
    )


def _create_lifecycle_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE automation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            summary TEXT,
            updated_at TEXT
        )
        """
    )


def _create_append_only_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            payload TEXT NOT NULL,
            note TEXT
        )
        """
    )


def _allowed_transitions() -> dict[str, list[str]]:
    return {
        "pending": ["running", "cancelled"],
        "running": ["completed", "failed", "cancelled"],
    }


def test_upsert_row_inserts_when_no_conflict(fresh_conn) -> None:
    conn = fresh_conn("upsert-insert.db")
    _create_upsert_table(conn)

    row_id = helix_db._upsert_row(
        conn,
        "session_telemetry",
        {"session_id": "sess-1", "tokens_used": 10, "model": "gpt-5.4"},
        "session_id",
    )
    conn.commit()
    row = conn.execute(
        "SELECT rowid AS row_id, * FROM session_telemetry WHERE session_id = ?",
        ("sess-1",),
    ).fetchone()

    assert row is not None
    assert row_id == row["row_id"]
    assert row["tokens_used"] == 10


def test_upsert_row_updates_on_conflict(fresh_conn) -> None:
    conn = fresh_conn("upsert-update.db")
    _create_upsert_table(conn)

    first_row_id = helix_db._upsert_row(
        conn,
        "session_telemetry",
        {"session_id": "sess-1", "tokens_used": 10, "model": "gpt-5.4"},
        "session_id",
    )
    second_row_id = helix_db._upsert_row(
        conn,
        "session_telemetry",
        {"session_id": "sess-1", "tokens_used": 42, "model": "gpt-5.5"},
        "session_id",
    )
    conn.commit()
    rows = conn.execute("SELECT rowid, tokens_used, model FROM session_telemetry").fetchall()

    assert len(rows) == 1
    assert second_row_id == first_row_id
    assert rows[0]["tokens_used"] == 42
    assert rows[0]["model"] == "gpt-5.5"


def test_upsert_row_missing_conflict_column_raises(fresh_conn) -> None:
    conn = fresh_conn("upsert-missing-conflict.db")
    _create_upsert_table(conn)

    with pytest.raises(ValueError, match="missing conflict column: session_id"):
        helix_db._upsert_row(
            conn,
            "session_telemetry",
            {"tokens_used": 10, "model": "gpt-5.4"},
            "session_id",
        )


def test_upsert_row_preserves_other_columns(fresh_conn) -> None:
    conn = fresh_conn("upsert-preserve.db")
    _create_upsert_table(conn)

    helix_db._upsert_row(
        conn,
        "session_telemetry",
        {"session_id": "sess-1", "tokens_used": 10, "model": "gpt-5.4", "note": "keep"},
        "session_id",
    )
    helix_db._upsert_row(
        conn,
        "session_telemetry",
        {"session_id": "sess-1", "tokens_used": 20},
        "session_id",
    )
    conn.commit()
    row = conn.execute(
        "SELECT tokens_used, model, note FROM session_telemetry WHERE session_id = ?",
        ("sess-1",),
    ).fetchone()

    assert row["tokens_used"] == 20
    assert row["model"] == "gpt-5.4"
    assert row["note"] == "keep"


def test_transition_valid(fresh_conn) -> None:
    conn = fresh_conn("transition-valid.db")
    _create_lifecycle_table(conn)
    cursor = conn.execute(
        "INSERT INTO automation_runs (status, summary, updated_at) VALUES (?, ?, ?)",
        ("pending", "queued", "2026-05-16T00:00:00"),
    )
    row_id = int(cursor.lastrowid)

    result = helix_db._transition_lifecycle_status(
        conn,
        "automation_runs",
        row_id,
        "pending",
        "running",
        _allowed_transitions(),
    )
    conn.commit()
    row = conn.execute("SELECT status, updated_at FROM automation_runs WHERE id = ?", (row_id,)).fetchone()

    assert result is True
    assert row["status"] == "running"
    assert row["updated_at"] != "2026-05-16T00:00:00"


def test_transition_invalid_raises(fresh_conn) -> None:
    conn = fresh_conn("transition-invalid.db")
    _create_lifecycle_table(conn)
    cursor = conn.execute("INSERT INTO automation_runs (status) VALUES (?)", ("pending",))

    with pytest.raises(sqlite3.IntegrityError, match=r"invalid lifecycle transition: pending -> completed"):
        helix_db._transition_lifecycle_status(
            conn,
            "automation_runs",
            int(cursor.lastrowid),
            "pending",
            "completed",
            _allowed_transitions(),
        )


def test_transition_status_mismatch_raises(fresh_conn) -> None:
    conn = fresh_conn("transition-mismatch.db")
    _create_lifecycle_table(conn)
    cursor = conn.execute("INSERT INTO automation_runs (status) VALUES (?)", ("running",))

    with pytest.raises(sqlite3.IntegrityError, match=r"status mismatch: expected pending got running"):
        helix_db._transition_lifecycle_status(
            conn,
            "automation_runs",
            int(cursor.lastrowid),
            "pending",
            "completed",
            _allowed_transitions(),
        )


def test_transition_from_terminal_raises(fresh_conn) -> None:
    conn = fresh_conn("transition-terminal.db")
    _create_lifecycle_table(conn)
    cursor = conn.execute("INSERT INTO automation_runs (status) VALUES (?)", ("completed",))

    with pytest.raises(sqlite3.IntegrityError, match=r"invalid lifecycle transition: completed -> running"):
        helix_db._transition_lifecycle_status(
            conn,
            "automation_runs",
            int(cursor.lastrowid),
            "completed",
            "running",
            _allowed_transitions(),
        )


def test_trigger_delete_rejected(fresh_conn) -> None:
    conn = fresh_conn("trigger-delete.db")
    _create_append_only_table(conn)
    helix_db._create_append_only_trigger(conn, "audit_log")
    cursor = conn.execute(
        "INSERT INTO audit_log (status, payload, note) VALUES (?, ?, ?)",
        ("pending", "{}", "hello"),
    )

    with pytest.raises(sqlite3.IntegrityError, match="audit_log is append-only"):
        conn.execute("DELETE FROM audit_log WHERE id = ?", (int(cursor.lastrowid),))


def test_trigger_immutable_columns(fresh_conn) -> None:
    conn = fresh_conn("trigger-immutable.db")
    _create_append_only_table(conn)
    helix_db._create_append_only_trigger(conn, "audit_log", immutable_columns=["payload"])
    cursor = conn.execute(
        "INSERT INTO audit_log (status, payload, note) VALUES (?, ?, ?)",
        ("pending", '{"a":1}', "hello"),
    )

    with pytest.raises(sqlite3.IntegrityError, match=r"audit_log\.payload is immutable"):
        conn.execute(
            "UPDATE audit_log SET payload = ? WHERE id = ?",
            ('{"a":2}', int(cursor.lastrowid)),
        )


def test_trigger_terminal_final(fresh_conn) -> None:
    conn = fresh_conn("trigger-terminal.db")
    _create_append_only_table(conn)
    helix_db._create_append_only_trigger(
        conn,
        "audit_log",
        terminal_status_column="status",
        terminal_values=["completed", "failed", "cancelled"],
    )
    cursor = conn.execute(
        "INSERT INTO audit_log (status, payload, note) VALUES (?, ?, ?)",
        ("completed", '{"a":1}', "hello"),
    )

    with pytest.raises(sqlite3.IntegrityError, match="audit_log terminal status is final"):
        conn.execute(
            "UPDATE audit_log SET note = ? WHERE id = ?",
            ("changed", int(cursor.lastrowid)),
        )


def test_trigger_idempotent(fresh_conn) -> None:
    conn = fresh_conn("trigger-idempotent.db")
    _create_append_only_table(conn)

    helix_db._create_append_only_trigger(
        conn,
        "audit_log",
        immutable_columns=["payload"],
        terminal_status_column="status",
        terminal_values=["completed"],
    )
    helix_db._create_append_only_trigger(
        conn,
        "audit_log",
        immutable_columns=["payload"],
        terminal_status_column="status",
        terminal_values=["completed"],
    )

    trigger_names = [
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = ? ORDER BY name",
            ("audit_log",),
        ).fetchall()
    ]

    assert trigger_names == [
        "audit_log_no_delete",
        "audit_log_payload_immutable",
        "audit_log_terminal_final",
    ]


def test_trigger_empty_immutable_columns_raises(fresh_conn) -> None:
    conn = fresh_conn("trigger-empty-immutable.db")
    _create_append_only_table(conn)

    with pytest.raises(ValueError, match="immutable_columns must not be empty"):
        helix_db._create_append_only_trigger(conn, "audit_log", immutable_columns=[])


def test_trigger_terminal_values_require_status_column(fresh_conn) -> None:
    conn = fresh_conn("trigger-terminal-validation.db")
    _create_append_only_table(conn)

    with pytest.raises(ValueError, match="terminal_status_column is required when terminal_values is set"):
        helix_db._create_append_only_trigger(conn, "audit_log", terminal_values=["completed"])
