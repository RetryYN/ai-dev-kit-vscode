import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


@pytest.fixture
def v23_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / ".helix" / "test_v24.db"
    helix_db.init_db(str(db_path))
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def v24_db(v23_db: sqlite3.Connection) -> sqlite3.Connection:
    helix_db._migrate_v23_to_v24(v23_db)
    return v23_db


def _insert_design_sprint_entry(
    conn: sqlite3.Connection,
    *,
    plan_id: str = "PLAN-070",
    sprint_id: str = "M3-SprintB",
    sprint_type: str = "functional",
    layer: str = "functional",
    drive: str = "db",
    track: str = "db",
    pair_status: str = "paired",
    raw_meta: str = '{"scope":"v24-test"}',
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO design_sprint_entries (
            plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, raw_meta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, raw_meta),
    )
    return int(cursor.lastrowid)


def _insert_drive_decision(
    conn: sqlite3.Connection,
    *,
    source_entry_id: int,
    target_entry_id: int,
    decision: str = "preserved",
    decided_by: str = "tl",
    reason: str = "carry forward",
    reopen_condition: str | None = None,
    lifecycle_status: str = "observed",
    direction: str = "forward",
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO design_sprint_drive_decisions (
            source_entry_id,
            target_entry_id,
            decision,
            decided_by,
            reason,
            reopen_condition,
            lifecycle_status,
            direction
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_entry_id,
            target_entry_id,
            decision,
            decided_by,
            reason,
            reopen_condition,
            lifecycle_status,
            direction,
        ),
    )
    return int(cursor.lastrowid)


def test_v23_to_v24_migrate_succeeds(v23_db: sqlite3.Connection) -> None:
    helix_db._migrate_v23_to_v24(v23_db)

    table = v23_db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'design_sprint_drive_decisions'"
    ).fetchone()
    columns = {
        row["name"] for row in v23_db.execute("PRAGMA table_info(design_sprint_drive_decisions)").fetchall()
    }
    indexes = {
        row["name"]
        for row in v23_db.execute("PRAGMA index_list(design_sprint_drive_decisions)").fetchall()
    }

    assert table is not None
    assert {
        "id",
        "source_entry_id",
        "target_entry_id",
        "decision",
        "decided_by",
        "reason",
        "reopen_condition",
        "lifecycle_status",
        "direction",
        "created_at",
    } <= columns
    assert {"idx_dsdd_source", "idx_dsdd_target", "idx_dsdd_decision"} <= indexes


def test_v24_migrate_is_idempotent(v23_db: sqlite3.Connection) -> None:
    helix_db._migrate_v23_to_v24(v23_db)
    helix_db._migrate_v23_to_v24(v23_db)

    tables = v23_db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'design_sprint_drive_decisions'
        """
    ).fetchall()
    columns = [row["name"] for row in v23_db.execute("PRAGMA table_info(design_sprint_drive_decisions)").fetchall()]
    indexes = [row["name"] for row in v23_db.execute("PRAGMA index_list(design_sprint_drive_decisions)").fetchall()]

    assert len(tables) == 1
    assert columns.count("lifecycle_status") == 1
    assert columns.count("direction") == 1
    assert indexes.count("idx_dsdd_source") == 1
    assert indexes.count("idx_dsdd_target") == 1
    assert indexes.count("idx_dsdd_decision") == 1


def test_v24_decision_enum_check(v24_db: sqlite3.Connection) -> None:
    source_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-1")
    target_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-2")

    with pytest.raises(sqlite3.IntegrityError):
        _insert_drive_decision(
            v24_db,
            source_entry_id=source_entry_id,
            target_entry_id=target_entry_id,
            decision="rejected",
        )


def test_v24_source_entry_id_fk(v24_db: sqlite3.Connection) -> None:
    target_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-target")

    with pytest.raises(sqlite3.IntegrityError):
        _insert_drive_decision(
            v24_db,
            source_entry_id=999999,
            target_entry_id=target_entry_id,
        )


def test_v24_lifecycle_status_enum_check(v24_db: sqlite3.Connection) -> None:
    source_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-3")
    target_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-4")

    with pytest.raises(sqlite3.IntegrityError):
        _insert_drive_decision(
            v24_db,
            source_entry_id=source_entry_id,
            target_entry_id=target_entry_id,
            lifecycle_status="unknown",
        )


def test_v24_direction_enum_check(v24_db: sqlite3.Connection) -> None:
    source_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-5")
    target_entry_id = _insert_design_sprint_entry(v24_db, sprint_id="M3-SprintB-6")

    with pytest.raises(sqlite3.IntegrityError):
        _insert_drive_decision(
            v24_db,
            source_entry_id=source_entry_id,
            target_entry_id=target_entry_id,
            direction="lateral",
        )
