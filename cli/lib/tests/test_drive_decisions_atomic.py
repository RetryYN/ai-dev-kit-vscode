import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "helix.db"
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)
    return db_path


def _seed_entry(db_path: Path, plan_id: str, drive: str) -> int:
    with helix_db._write_connection(str(db_path)) as conn:
        cursor = conn.execute(
            """
            INSERT INTO design_sprint_entries (
                plan_id, sprint_type, layer, drive, track, pair_status, raw_meta
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                "functional",
                "functional",
                drive,
                "shared",
                "paired",
                '{"g2_evidence_preserved": true}',
            ),
        )
        return int(cursor.lastrowid)


def test_insert_drive_decision_rolls_back_when_insert_aborts(temp_db: Path) -> None:
    """INSERT 中に例外が起きても、同一 transaction の変更が all-or-nothing で rollback されることを確認する。"""
    plan_id = "PLAN-300"
    source_entry_id = _seed_entry(temp_db, plan_id, "be")
    target_entry_id = _seed_entry(temp_db, plan_id, "fe")

    with helix_db._write_connection(str(temp_db)) as conn:
        conn.execute(
            """
            CREATE TRIGGER fail_drive_decision_insert
            BEFORE INSERT ON design_sprint_drive_decisions
            WHEN NEW.reason = 'atomic rollback test'
            BEGIN
                SELECT RAISE(ABORT, 'injected drive decision insert failure');
            END
            """
        )
        conn.commit()

    with pytest.raises(sqlite3.IntegrityError, match="injected drive decision insert failure"):
        with helix_db._write_connection(str(temp_db)) as conn:
            conn.execute(
                """
                INSERT INTO design_sprint_entries (
                    plan_id, sprint_type, layer, drive, track, pair_status, raw_meta
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    "functional",
                    "functional",
                    "db",
                    "shared",
                    "paired",
                    "{}",
                ),
            )
            helix_db.insert_drive_decision(
                conn,
                plan_id=plan_id,
                source_entry_id=source_entry_id,
                target_entry_id=target_entry_id,
                decision="preserved",
                reason="atomic rollback test",
            )

    with sqlite3.connect(str(temp_db)) as conn:
        decision_count = conn.execute(
            "SELECT COUNT(*) FROM design_sprint_drive_decisions"
        ).fetchone()[0]
        entry_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM design_sprint_entries
            WHERE plan_id = ?
            """,
            (plan_id,),
        ).fetchone()[0]

    assert decision_count == 0
    assert entry_count == 2


def test_same_entry_id_raises_and_no_row_inserted(temp_db: Path) -> None:
    """source_entry_id == target_entry_id の場合、ValueError で INSERT されないことを確認する。"""
    plan_id = "PLAN-301"
    entry_id = _seed_entry(temp_db, plan_id, "be")

    with pytest.raises(ValueError, match="must differ"):
        with helix_db._write_connection(str(temp_db)) as conn:
            helix_db.insert_drive_decision(
                conn,
                plan_id=plan_id,
                source_entry_id=entry_id,
                target_entry_id=entry_id,
                decision="preserved",
                reason="same-entry test",
            )

    with sqlite3.connect(str(temp_db)) as conn:
        decision_count = conn.execute(
            "SELECT COUNT(*) FROM design_sprint_drive_decisions"
        ).fetchone()[0]

    assert decision_count == 0


def test_nonexistent_source_entry_raises_and_rollback(temp_db: Path) -> None:
    """存在しない source_entry_id では ValueError が発生し、transaction が rollback されることを確認する。"""
    plan_id = "PLAN-302"
    target_entry_id = _seed_entry(temp_db, plan_id, "fe")

    with pytest.raises(ValueError, match="does not exist"):
        with helix_db._write_connection(str(temp_db)) as conn:
            conn.execute(
                """
                INSERT INTO design_sprint_entries (
                    plan_id, sprint_type, layer, drive, track, pair_status, raw_meta
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    "functional",
                    "functional",
                    "db",
                    "shared",
                    "paired",
                    "{}",
                ),
            )
            helix_db.insert_drive_decision(
                conn,
                plan_id=plan_id,
                source_entry_id=99999,
                target_entry_id=target_entry_id,
                decision="preserved",
                reason="nonexistent source",
            )

    with sqlite3.connect(str(temp_db)) as conn:
        decision_count = conn.execute(
            "SELECT COUNT(*) FROM design_sprint_drive_decisions"
        ).fetchone()[0]
        entry_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM design_sprint_entries
            WHERE plan_id = ?
            """,
            (plan_id,),
        ).fetchone()[0]

    assert decision_count == 0
    assert entry_count == 1
