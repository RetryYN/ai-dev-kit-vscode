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


def _seed_entry(db_path: Path, plan_id: str, drive: str, pair_status: str = "paired") -> int:
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
                pair_status,
                '{"g2_evidence_preserved": true}',
            ),
        )
        return int(cursor.lastrowid)


def test_multi_drive_entries_coexist(temp_db: Path) -> None:
    """同一 plan_id に be/fe/fullstack の 3 entry が並存できることを検証。"""
    plan_id = "PLAN-100"
    be_id = _seed_entry(temp_db, plan_id, "be")
    fe_id = _seed_entry(temp_db, plan_id, "fe")
    fs_id = _seed_entry(temp_db, plan_id, "fullstack")

    with sqlite3.connect(str(temp_db)) as conn:
        rows = conn.execute(
            "SELECT drive FROM design_sprint_entries WHERE plan_id = ? ORDER BY drive",
            (plan_id,),
        ).fetchall()

    drives = [row[0] for row in rows]
    assert drives == ["be", "fe", "fullstack"]
    assert len({be_id, fe_id, fs_id}) == 3


def test_multi_drive_decision_records_all_pairs(temp_db: Path) -> None:
    """multi-drive entries 間の drive_decision を全 pair で記録できることを検証。"""
    plan_id = "PLAN-101"
    be_id = _seed_entry(temp_db, plan_id, "be")
    fe_id = _seed_entry(temp_db, plan_id, "fe")
    fs_id = _seed_entry(temp_db, plan_id, "fullstack")

    pairs = [(be_id, fe_id), (be_id, fs_id), (fe_id, fs_id)]
    with helix_db._write_connection(str(temp_db)) as conn:
        for source, target in pairs:
            helix_db.insert_drive_decision(
                conn,
                plan_id=plan_id,
                source_entry_id=source,
                target_entry_id=target,
                decision="preserved",
                reason="multi-drive coexistence test",
            )

    with sqlite3.connect(str(temp_db)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM design_sprint_drive_decisions").fetchone()[0]

    assert count == 3
