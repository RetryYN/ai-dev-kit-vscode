import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def test_migrate_v18_to_v19_adds_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()}
    finally:
        conn.close()

    assert {"qa_result", "security_audit", "design_decision"} <= columns


def test_migrate_v18_to_v19_creates_observation_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert {"sprint_metrics", "phase_gate_runs"} <= tables


def test_migrate_v18_to_v19_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    helix_db.init_db(str(db_path))
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        version_rows = conn.execute(
            "SELECT version FROM schema_version WHERE version = 19"
        ).fetchall()
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()]
    finally:
        conn.close()

    assert len(version_rows) == 1
    assert columns.count("qa_result") == 1
    assert columns.count("security_audit") == 1
    assert columns.count("design_decision") == 1


def test_migrate_v18_to_v19_preserves_existing_entries(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('test-1', 'code', 'initial', 'test')"
        )
        conn.commit()
    finally:
        conn.close()

    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        rows = conn.execute("SELECT id FROM entries WHERE id = 'test-1'").fetchall()
    finally:
        conn.close()

    assert len(rows) == 1


def test_current_schema_version_is_33() -> None:
    assert helix_db.CURRENT_SCHEMA_VERSION == 33
