import json
import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


@pytest.fixture
def automation_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / ".helix" / "automation-runs.db"
    helix_db.init_db(str(db_path))
    conn = helix_db.get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def test_insert_automation_run_transitions_to_running(automation_db: sqlite3.Connection) -> None:
    run_id = helix_db.insert_automation_run(
        automation_db,
        "helix-push",
        "push",
        {"branch": "main", "remote": "origin"},
    )
    row = automation_db.execute(
        "SELECT * FROM automation_runs WHERE id = ?",
        (run_id,),
    ).fetchone()

    assert row is not None
    assert row["run_kind"] == "push"
    assert row["trigger_actor"] == "system"
    assert row["status"] == "running"
    assert row["started_at"]
    assert row["ended_at"] is None
    assert row["plan_id"] is None
    assert json.loads(row["summary"]) == {
        "branch": "main",
        "remote": "origin",
        "trigger_source": "helix-push",
    }


def test_insert_automation_run_uses_plan_id_from_metadata(automation_db: sqlite3.Connection) -> None:
    run_id = helix_db.insert_automation_run(
        automation_db,
        "helix-pr",
        "pr",
        {"plan_id": "PLAN-072", "base": "main"},
    )
    row = automation_db.execute(
        "SELECT plan_id, summary FROM automation_runs WHERE id = ?",
        (run_id,),
    ).fetchone()

    assert row is not None
    assert row["plan_id"] == "PLAN-072"
    assert json.loads(row["summary"]) == {
        "base": "main",
        "plan_id": "PLAN-072",
        "trigger_source": "helix-pr",
    }


def test_complete_automation_run_marks_completed(automation_db: sqlite3.Connection) -> None:
    run_id = helix_db.insert_automation_run(automation_db, "helix-push", "push")

    helix_db.complete_automation_run(automation_db, run_id, "completed")

    row = automation_db.execute(
        "SELECT status, exit_code, ended_at, last_error FROM automation_runs WHERE id = ?",
        (run_id,),
    ).fetchone()

    assert row is not None
    assert row["status"] == "completed"
    assert row["exit_code"] == 0
    assert row["ended_at"]
    assert row["last_error"] is None


def test_complete_automation_run_marks_failed_with_error(automation_db: sqlite3.Connection) -> None:
    run_id = helix_db.insert_automation_run(automation_db, "helix-pr", "pr")

    helix_db.complete_automation_run(automation_db, run_id, "failed", "gate validation failed")

    row = automation_db.execute(
        "SELECT status, exit_code, ended_at, last_error FROM automation_runs WHERE id = ?",
        (run_id,),
    ).fetchone()

    assert row is not None
    assert row["status"] == "failed"
    assert row["exit_code"] == 1
    assert row["ended_at"]
    assert row["last_error"] == "gate validation failed"


def test_insert_automation_run_rejects_non_dict_metadata(automation_db: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="metadata must be a dict"):
        helix_db.insert_automation_run(automation_db, "helix-push", "push", "nope")  # type: ignore[arg-type]
