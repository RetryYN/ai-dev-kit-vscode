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


def test_insert_drive_decision_is_not_idempotent_without_caller_guard(temp_db: Path) -> None:
    """現状 schema には UNIQUE 制約がないため、同じ pair を複数回 INSERT すると複数行になる。"""
    plan_id = "PLAN-200"
    source_entry_id = _seed_entry(temp_db, plan_id, "be")
    target_entry_id = _seed_entry(temp_db, plan_id, "fe")

    with helix_db._write_connection(str(temp_db)) as conn:
        for _ in range(3):
            helix_db.insert_drive_decision(
                conn,
                plan_id=plan_id,
                source_entry_id=source_entry_id,
                target_entry_id=target_entry_id,
                decision="preserved",
                reason="idempotent test",
            )

    with sqlite3.connect(str(temp_db)) as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM design_sprint_drive_decisions
            WHERE source_entry_id = ? AND target_entry_id = ? AND decision = ?
            """,
            (source_entry_id, target_entry_id, "preserved"),
        ).fetchone()[0]

    assert count == 3, "現状は non-idempotent (caller が重複防止する責務)"


def test_caller_can_implement_idempotency_via_select_then_insert(temp_db: Path) -> None:
    """caller 側で SELECT してから INSERT する pattern なら idempotent に扱える。"""
    plan_id = "PLAN-201"
    source_entry_id = _seed_entry(temp_db, plan_id, "be")
    target_entry_id = _seed_entry(temp_db, plan_id, "fe")

    def insert_if_not_exists() -> None:
        with helix_db._write_connection(str(temp_db)) as conn:
            existing = conn.execute(
                """
                SELECT id
                FROM design_sprint_drive_decisions
                WHERE source_entry_id = ? AND target_entry_id = ? AND decision = ?
                """,
                (source_entry_id, target_entry_id, "preserved"),
            ).fetchone()
            if existing is None:
                helix_db.insert_drive_decision(
                    conn,
                    plan_id=plan_id,
                    source_entry_id=source_entry_id,
                    target_entry_id=target_entry_id,
                    decision="preserved",
                    reason="caller-side idempotency",
                )

    for _ in range(3):
        insert_if_not_exists()

    with sqlite3.connect(str(temp_db)) as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM design_sprint_drive_decisions
            WHERE source_entry_id = ? AND target_entry_id = ? AND decision = ?
            """,
            (source_entry_id, target_entry_id, "preserved"),
        ).fetchone()[0]

    assert count == 1, "caller-side guard で idempotent 実現"
