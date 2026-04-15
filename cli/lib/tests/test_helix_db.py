import contextlib
import io
import json
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _fetch_one(db_path: Path, query: str, params: tuple = ()) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()


def _fetch_all(db_path: Path, query: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def _seed_history(db_path: Path) -> tuple[int, int]:
    helix_db.record_task(
        str(db_path),
        {
            "task_id": "T100",
            "task_type": "review-security",
            "plan_goal": "ship safely",
            "role": "qa",
            "status": "completed",
            "started_at": "2025-01-01T00:00:00",
            "output_log": "done",
        },
    )
    run_id = int(_fetch_one(db_path, "SELECT id FROM task_runs ORDER BY id DESC LIMIT 1")["id"])
    helix_db.record_action(
        str(db_path),
        {
            "task_run_id": run_id,
            "action_index": 1,
            "action_type": "pytest",
            "action_desc": "run regression",
            "status": "passed",
            "evidence": "ok",
        },
    )
    action_id = int(_fetch_one(db_path, "SELECT id FROM action_logs ORDER BY id DESC LIMIT 1")["id"])
    helix_db.record_observation(
        str(db_path),
        {
            "task_run_id": run_id,
            "action_log_id": action_id,
            "action_type": "pytest",
            "expected_keywords": ["pass"],
            "matched_keywords": ["pass"],
            "passed": True,
            "reason": "",
        },
    )
    helix_db.record_feedback(
        str(db_path),
        {
            "task_run_id": run_id,
            "feedback_type": "correction",
            "category": "quality",
            "description": "Need more coverage",
            "impact": "medium",
            "resolution": "Added tests",
        },
    )
    return run_id, action_id


def test_init_db_creates_primary_tables(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()

    rows = _fetch_all(
        db_path,
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
    )
    names = {row["name"] for row in rows}

    assert {"task_runs", "action_logs", "observations", "feedback", "gate_runs", "requirements", "schema_version"} <= names


def test_init_db_records_current_schema_version(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()

    versions = _fetch_all(db_path, "SELECT version FROM schema_version ORDER BY version")

    assert [row["version"] for row in versions] == [2, 3, 4, 5]


def test_record_task_persists_json_payload(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()

    helix_db.record_task(
        str(db_path),
        {
            "task_id": "T001",
            "task_type": "research-library",
            "plan_goal": "Validate library",
            "role": "qa",
            "status": "completed",
            "started_at": "2025-01-01T00:00:00",
            "output_log": '{"ok": true}',
        },
    )

    row = _fetch_one(db_path, "SELECT * FROM task_runs WHERE task_id = ?", ("T001",))
    assert row["task_type"] == "research-library"
    assert row["plan_goal"] == "Validate library"
    assert row["output_log"] == '{"ok": true}'


def test_record_action_persists_json_payload(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    run_id, _ = _seed_history(db_path)
    capsys.readouterr()

    helix_db.record_action(
        str(db_path),
        {
            "task_run_id": run_id,
            "action_index": 2,
            "action_type": "fact-check",
            "action_desc": "verify API",
            "status": "failed",
            "evidence": '{"errors": 1}',
        },
    )

    row = _fetch_one(db_path, "SELECT * FROM action_logs WHERE action_index = 2")
    assert row["action_type"] == "fact-check"
    assert row["status"] == "failed"
    assert row["evidence"] == '{"errors": 1}'


def test_record_observation_serializes_keyword_lists(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    run_id, action_id = _seed_history(db_path)
    capsys.readouterr()

    helix_db.record_observation(
        str(db_path),
        {
            "task_run_id": run_id,
            "action_log_id": action_id,
            "action_type": "verify",
            "expected_keywords": ["alpha", "beta"],
            "matched_keywords": ["alpha"],
            "passed": False,
            "reason": "missing beta",
        },
    )

    row = _fetch_one(db_path, "SELECT * FROM observations ORDER BY id DESC LIMIT 1")
    assert json.loads(row["expected_keywords"]) == ["alpha", "beta"]
    assert json.loads(row["matched_keywords"]) == ["alpha"]
    assert row["passed"] == 0
    assert row["reason"] == "missing beta"


def test_record_feedback_persists_payload(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    run_id, _ = _seed_history(db_path)
    capsys.readouterr()

    helix_db.record_feedback(
        str(db_path),
        {
            "task_run_id": run_id,
            "feedback_type": "suggestion",
            "category": "scope",
            "description": "Add regression suite",
            "impact": "high",
            "resolution": "Planned",
        },
    )

    row = _fetch_one(db_path, "SELECT * FROM feedback ORDER BY id DESC LIMIT 1")
    assert row["feedback_type"] == "suggestion"
    assert row["category"] == "scope"
    assert row["impact"] == "high"


def test_latest_task_run_id_returns_latest_matching_row(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()

    helix_db.record_task(str(db_path), {"task_id": "T900", "task_type": "lint", "role": "qa"})
    first = int(capsys.readouterr().out.strip())
    helix_db.record_task(str(db_path), {"task_id": "T900", "task_type": "lint", "role": "qa"})
    second = int(capsys.readouterr().out.strip())

    helix_db.latest_task_run_id(str(db_path), "T900")
    assert capsys.readouterr().out.strip() == str(second)
    assert second > first


def test_report_summary_runs_without_exception(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    _seed_history(db_path)
    capsys.readouterr()

    helix_db.report(str(db_path), "summary")
    output = capsys.readouterr().out

    assert "HELIX Log Summary" in output
    assert "Tasks:" in output
    assert "Actions:" in output


def test_report_tasks_runs_without_exception(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    _seed_history(db_path)
    capsys.readouterr()

    helix_db.report(str(db_path), "tasks")
    output = capsys.readouterr().out

    assert "Task History" in output
    assert "review-security" in output


def test_report_actions_runs_without_exception(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    _seed_history(db_path)
    capsys.readouterr()

    helix_db.report(str(db_path), "actions")
    output = capsys.readouterr().out

    assert "Action Type Performance" in output
    assert "pytest" in output


def test_report_feedback_runs_without_exception(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    _seed_history(db_path)
    capsys.readouterr()

    helix_db.report(str(db_path), "feedback")
    output = capsys.readouterr().out

    assert "Feedback Analysis" in output
    assert "Need more coverage" in output


def test_report_quality_runs_without_exception(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    _seed_history(db_path)
    capsys.readouterr()

    helix_db.report(str(db_path), "quality")
    output = capsys.readouterr().out

    assert "Task Selection Quality" in output
    assert "review-security" in output


def test_migrate_from_v1_to_v5_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.execute("DROP TABLE IF EXISTS requirements")
    conn.execute("DROP TABLE IF EXISTS req_impl_map")
    conn.execute("DROP TABLE IF EXISTS req_test_map")
    conn.execute("DROP TABLE IF EXISTS req_changes")
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (1, '2025-01-01T00:00:00')"
    )
    conn.commit()

    helix_db.migrate(conn)
    helix_db.migrate(conn)

    versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")]
    requirement_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'req_%' OR name='requirements'"
        )
    }
    conn.close()

    assert versions == [1, 2, 3, 4, 5]
    assert {"requirements", "req_impl_map", "req_test_map", "req_changes"} <= requirement_tables


def test_migrate_from_v3_to_v5_recreates_tables_with_fk_and_keeps_data(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-v3.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)

    conn.execute("DROP TABLE IF EXISTS retro_items")
    conn.execute("DROP TABLE IF EXISTS interrupts")
    conn.execute("DROP TABLE IF EXISTS gate_runs")

    conn.execute(
        """
        CREATE TABLE gate_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate TEXT NOT NULL,
            result TEXT NOT NULL,
            fail_reasons TEXT DEFAULT '',
            retry_count INTEGER DEFAULT 0,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE interrupts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interrupt_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            classification TEXT NOT NULL,
            scope TEXT DEFAULT '',
            status TEXT NOT NULL,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            resolved_at TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE retro_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate TEXT NOT NULL,
            item_type TEXT NOT NULL,
            content TEXT NOT NULL,
            owner TEXT DEFAULT '',
            due TEXT DEFAULT '',
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        "INSERT INTO gate_runs (id, gate, result, fail_reasons, retry_count, duration_ms, created_at) VALUES (1, 'G2', 'pass', '', 0, 10, '2025-01-01T00:00:00')"
    )
    conn.execute(
        "INSERT INTO interrupts (id, interrupt_id, kind, classification, scope, status, duration_ms, created_at, resolved_at) VALUES (1, 'INT-001', 'incident', 'P1', 'core', 'closed', 55, '2025-01-01T00:01:00', '2025-01-01T00:02:00')"
    )
    conn.execute(
        "INSERT INTO retro_items (id, gate, item_type, content, owner, due, done, created_at) VALUES (1, 'G2', 'action', 'Add regression', 'tl', '2025-01-10', 0, '2025-01-01T00:03:00')"
    )
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (3, '2025-01-01T00:00:00')"
    )
    conn.commit()

    helix_db.migrate(conn)
    versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")]

    gate_runs_cols = {row[1] for row in conn.execute("PRAGMA table_info(gate_runs)")}
    interrupts_cols = {row[1] for row in conn.execute("PRAGMA table_info(interrupts)")}
    retro_cols = {row[1] for row in conn.execute("PRAGMA table_info(retro_items)")}

    gate_runs_fk_tables = {row[2] for row in conn.execute("PRAGMA foreign_key_list(gate_runs)")}
    interrupts_fk_tables = {row[2] for row in conn.execute("PRAGMA foreign_key_list(interrupts)")}
    retro_fk_tables = {row[2] for row in conn.execute("PRAGMA foreign_key_list(retro_items)")}

    migrated_gate = conn.execute(
        "SELECT gate, task_run_id FROM gate_runs WHERE id = 1"
    ).fetchone()
    migrated_interrupt = conn.execute(
        "SELECT interrupt_id, task_run_id FROM interrupts WHERE id = 1"
    ).fetchone()
    migrated_retro = conn.execute(
        "SELECT gate, gate_name, gate_run_id FROM retro_items WHERE id = 1"
    ).fetchone()
    conn.close()

    assert versions == [3, 4, 5]
    assert "task_run_id" in gate_runs_cols
    assert "task_run_id" in interrupts_cols
    assert {"gate_name", "gate_run_id"} <= retro_cols
    assert "task_runs" in gate_runs_fk_tables
    assert "task_runs" in interrupts_fk_tables
    assert "gate_runs" in retro_fk_tables
    assert migrated_gate == ("G2", None)
    assert migrated_interrupt == ("INT-001", None)
    assert migrated_retro == ("G2", "G2", None)


def test_migrate_from_v4_to_v5_creates_skill_usage_table(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-v4.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.execute("DROP TABLE IF EXISTS skill_usage")
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (4, '2025-01-01T00:00:00')"
    )
    conn.commit()

    helix_db.migrate(conn)
    versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")]
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='skill_usage'"
    ).fetchone()
    indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name IN ('idx_skill_usage_skill', 'idx_skill_usage_outcome')"
        ).fetchall()
    }
    conn.close()

    assert versions == [4, 5]
    assert table is not None
    assert {"idx_skill_usage_skill", "idx_skill_usage_outcome"} <= indexes


def test_export_json_writes_valid_json(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    _seed_history(db_path)
    capsys.readouterr()

    output_path = tmp_path / "exports" / "helix.json"
    helix_db.export_json(str(db_path), str(output_path))
    capsys.readouterr()

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert "task_runs" in payload
    assert "action_logs" in payload
    assert payload["feedback"][0]["description"] == "Need more coverage"
