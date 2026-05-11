import json
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _fetch_one(db_path: Path, query: str, params: tuple = ()) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(query, params).fetchone()
        assert row is not None
        return row
    finally:
        conn.close()


def _create_v15_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(helix_db.SCHEMA)
        conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
        conn.executescript(helix_db.CODE_INDEX_SCHEMA_V15)
        for version in range(2, 16):
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
                (version,),
            )
        conn.execute(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                "helix-db.record-task",
                "cli/lib",
                "task record helper",
                "cli/lib/helix_db.py",
                1304,
                1304,
                "coverage_eligible",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_migrate_v15_to_v16_keeps_code_index_rows(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    _create_v15_db(db_path)

    helix_db.init_db(str(db_path))
    capsys.readouterr()

    table_row = _fetch_one(
        db_path,
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'invocation_log'",
    )
    preserved = _fetch_one(
        db_path,
        "SELECT id, path FROM code_index WHERE id = ?",
        ("helix-db.record-task",),
    )

    assert table_row["name"] == "invocation_log"
    assert preserved["path"] == "cli/lib/helix_db.py"


def test_record_invocation_inserts_selectable_row(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    capsys.readouterr()

    helix_db.record_invocation(
        str(db_path),
        {
            "timestamp": "2026-05-12T12:00:00",
            "type": "codex",
            "role": "se",
            "model": "gpt-5.4",
            "task_id": "W-1a",
            "plan_id": "PLAN-063",
            "sprint": ".1a",
            "input_bytes": 120,
            "output_bytes": 48,
            "duration_ms": 2500,
            "decision": "passed",
            "cost_cents": 1.25,
            "raw_meta": {
                "role": "se",
                "model": "gpt-5.4",
                "task_id": "W-1a",
                "plan_id": "PLAN-063",
                "sprint": ".1a",
                "decision": "passed",
                "duration_ms": 2500,
                "cost_cents": 1.25,
                "prompt_text": "must not persist",
            },
        },
    )
    capsys.readouterr()

    row = _fetch_one(
        db_path,
        "SELECT type, role, model, plan_id, task_id, duration_ms, decision, raw_meta FROM invocation_log",
    )
    raw_meta = json.loads(row["raw_meta"])

    assert row["type"] == "codex"
    assert row["role"] == "se"
    assert row["model"] == "gpt-5.4"
    assert row["plan_id"] == "PLAN-063"
    assert row["task_id"] == "W-1a"
    assert row["duration_ms"] == 2500
    assert row["decision"] == "passed"
    assert raw_meta == {
        "role": "se",
        "model": "gpt-5.4",
        "task_id": "W-1a",
        "plan_id": "PLAN-063",
        "sprint": ".1a",
        "decision": "passed",
        "cost_cents": 1.25,
        "duration_ms": 2500,
    }


def test_redact_meta_allowlist_and_secret_patterns() -> None:
    redacted = helix_db._redact_meta(
        {
            "role": "se",
            "model": "gpt-5.4",
            "task_id": "W-1a " + "sk-" + ("X" * 24),
            "plan_id": "PLAN-063",
            "sprint": ".1a Bearer secret-token",
            "decision": "passed token=abc123",
            "cost_cents": 1.5,
            "duration_ms": 3210,
            "prompt_text": "drop me",
            "secret_blob": "sk-should-not-survive",
        }
    )

    assert redacted == {
        "role": "se",
        "model": "gpt-5.4",
        "task_id": "W-1a [REDACTED]",
        "plan_id": "PLAN-063",
        "sprint": ".1a [REDACTED]",
        "decision": "passed [REDACTED]",
        "cost_cents": 1.5,
        "duration_ms": 3210,
    }
