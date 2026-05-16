import json
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _insert_entry(
    db_path: Path,
    *,
    plan_id: str = "PLAN-072",
    drive: str,
    pair_status: str = "paired",
    raw_meta: dict | None = None,
) -> int:
    conn = helix_db.get_connection(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO design_sprint_entries (
                plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, raw_meta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                f"{drive}-sprint",
                "functional",
                "functional",
                drive,
                "shared",
                pair_status,
                json.dumps(raw_meta or {}, ensure_ascii=False, sort_keys=True),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def test_insert_drive_decision_records_row(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    source_entry_id = _insert_entry(db_path, drive="be", raw_meta={"g2_evidence_preserved": True})
    target_entry_id = _insert_entry(db_path, drive="fe", raw_meta={"g2_evidence_preserved": True})

    conn = helix_db.get_connection(db_path)
    try:
        decision_id = helix_db.insert_drive_decision(
            conn,
            "PLAN-072",
            source_entry_id,
            target_entry_id,
            "preserved",
            "pair_status=paired and evidence preserved",
            "forward",
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM design_sprint_drive_decisions WHERE id = ?",
            (decision_id,),
        ).fetchone()
    finally:
        conn.close()

    assert decision_id > 0
    assert row["source_entry_id"] == source_entry_id
    assert row["target_entry_id"] == target_entry_id
    assert row["decision"] == "preserved"
    assert row["reason"] == "pair_status=paired and evidence preserved"
    if "decided_by" in row.keys():
        assert row["decided_by"] == "se"
    if "direction" in row.keys():
        assert row["direction"] == "forward"


def test_insert_drive_decision_rejects_invalid_decision(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    source_entry_id = _insert_entry(db_path, drive="be")
    target_entry_id = _insert_entry(db_path, drive="fe")

    conn = helix_db.get_connection(db_path)
    try:
        with pytest.raises(ValueError, match="invalid decision"):
            helix_db.insert_drive_decision(
                conn,
                "PLAN-072",
                source_entry_id,
                target_entry_id,
                "blocked",
            )
    finally:
        conn.close()


def test_insert_drive_decision_accepts_waived(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    source_entry_id = _insert_entry(db_path, drive="fe")
    target_entry_id = _insert_entry(db_path, drive="fullstack", pair_status="waived")

    conn = helix_db.get_connection(db_path)
    try:
        decision_id = helix_db.insert_drive_decision(
            conn,
            "PLAN-072",
            source_entry_id,
            target_entry_id,
            "waived",
            "PM waiver recorded",
        )
        conn.commit()
        row = conn.execute(
            "SELECT decision, reason FROM design_sprint_drive_decisions WHERE id = ?",
            (decision_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["decision"] == "waived"
    assert row["reason"] == "PM waiver recorded"


def test_insert_drive_decision_rejects_cross_plan_target(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    source_entry_id = _insert_entry(db_path, plan_id="PLAN-072", drive="fe")
    target_entry_id = _insert_entry(db_path, plan_id="PLAN-999", drive="fullstack")

    conn = helix_db.get_connection(db_path)
    try:
        with pytest.raises(ValueError, match="target_entry_id does not belong to plan_id"):
            helix_db.insert_drive_decision(
                conn,
                "PLAN-072",
                source_entry_id,
                target_entry_id,
                "failed",
                "cross-plan target",
            )
    finally:
        conn.close()
