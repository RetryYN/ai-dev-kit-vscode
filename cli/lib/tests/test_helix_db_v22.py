import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _build_legacy_v21_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.executescript(helix_db.ACCURACY_SCORE_SCHEMA)
    conn.executescript(helix_db.INFRA_SCHEMA_V9)
    conn.executescript(helix_db.AUDIT_DECISIONS_SCHEMA_V10)
    helix_db._migrate_v10_to_v11(conn)
    helix_db._migrate_v11_to_v12(conn)
    helix_db._migrate_v12_to_v13(conn)
    helix_db._migrate_v13_to_v14(conn)
    helix_db._migrate_v14_to_v15(conn)
    helix_db._migrate_v15_to_v16(conn)
    helix_db._migrate_v16_to_v17(conn)
    helix_db._migrate_v17_to_v18(conn)
    helix_db._migrate_v18_to_v19(conn)
    helix_db._migrate_v19_to_v20(conn)
    helix_db._migrate_v20_to_v21(conn)
    conn.execute(
        """
        INSERT INTO design_sprint_entries (plan_id, sprint_type, layer, drive)
        VALUES ('PLAN-TEST', 'functional', 'functional', 'be')
        """
    )
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (21, '2026-05-15T00:00:00')"
    )
    conn.commit()
    return conn


def test_migrate_v21_to_current_adds_drive_switch_and_correction_columns(tmp_path: Path) -> None:
    conn = _build_legacy_v21_db(tmp_path / "legacy-v21.db")
    try:
        helix_db.migrate(conn)
        columns = {row[1]: row[4] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()}
        row = conn.execute(
            """
            SELECT previous_drive, drive_switch_reason, status_on_switch
            FROM design_sprint_entries
            WHERE plan_id = 'PLAN-TEST'
            """
        ).fetchone()
        versions = [entry[0] for entry in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()]
    finally:
        conn.close()

    assert columns["previous_drive"] is None
    assert columns["drive_switch_reason"] is None
    assert columns["status_on_switch"] is None
    assert columns["supersedes_entry_id"] is None
    assert columns["correction_reason"] is None
    assert columns["voided_at"] is None
    assert row == (None, None, None)
    assert versions == list(range(21, helix_db.CURRENT_SCHEMA_VERSION + 1))


def test_migrate_v21_to_v22_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "v22-idempotent.db"
    helix_db.init_db(str(db_path))
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        version_rows = conn.execute("SELECT version FROM schema_version WHERE version = 22").fetchall()
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()]
    finally:
        conn.close()

    assert len(version_rows) == 1
    assert columns.count("previous_drive") == 1
    assert columns.count("drive_switch_reason") == 1
    assert columns.count("status_on_switch") == 1


def test_current_schema_version_is_at_least_32() -> None:
    assert helix_db.CURRENT_SCHEMA_VERSION >= 32
