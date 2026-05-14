from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _seed_functional_entries(db_path: Path, drive: str, statuses: list[str]) -> None:
    conn = helix_db.get_connection(db_path)
    try:
        for idx, status in enumerate(statuses, start=1):
            conn.execute(
                """
                INSERT INTO design_sprint_entries (
                    plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, freeze_gate, subgate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("PLAN-100", f"SPRINT-{idx}", "functional", "functional", drive, "shared", status, "G3", "functional_freeze"),
            )
        conn.commit()
    finally:
        conn.close()


def _query_status(db_path: Path, drive: str) -> dict:
    conn = helix_db.get_connection(db_path)
    try:
        return helix_db.query_functional_freeze_status(conn, "PLAN-100", drive)
    finally:
        conn.close()


def test_query_functional_freeze_status_returns_missing_when_empty(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)

    result = _query_status(db_path, "fe")

    assert result == {
        "plan_id": "PLAN-100",
        "drive": "fe",
        "functional_pair_count": 0,
        "paired_count": 0,
        "pending_count": 0,
        "failed_count": 0,
        "verdict": "missing",
    }


def test_query_functional_freeze_status_returns_passed_when_all_paired(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "fe", ["paired", "paired"])

    result = _query_status(db_path, "fe")

    assert result["functional_pair_count"] == 2
    assert result["paired_count"] == 2
    assert result["pending_count"] == 0
    assert result["failed_count"] == 0
    assert result["verdict"] == "passed"


def test_query_functional_freeze_status_returns_failed_when_pending(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "fe", ["paired", "pending", "design_only", "test_only"])

    result = _query_status(db_path, "fe")

    assert result["functional_pair_count"] == 4
    assert result["paired_count"] == 1
    assert result["pending_count"] == 3
    assert result["failed_count"] == 0
    assert result["verdict"] == "failed"


def test_query_functional_freeze_status_returns_failed_when_failed(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "fe", ["paired", "failed"])

    result = _query_status(db_path, "fe")

    assert result["functional_pair_count"] == 2
    assert result["paired_count"] == 1
    assert result["pending_count"] == 0
    assert result["failed_count"] == 1
    assert result["verdict"] == "failed"
