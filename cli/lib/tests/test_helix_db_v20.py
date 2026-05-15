import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


LEGACY_CONTRACT_ENTRIES_SCHEMA = """
CREATE TABLE contract_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    symbol_id TEXT,
    version TEXT,
    schema_hash TEXT,
    breaking_change_flag INTEGER DEFAULT 0,
    introduced_plan TEXT,
    raw_spec TEXT
);
CREATE INDEX idx_contract_type ON contract_entries(contract_type);
CREATE INDEX idx_contract_breaking ON contract_entries(breaking_change_flag);
"""


def test_migrate_v19_to_current_creates_qa_tables_and_contract_design_level(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-v19.db"
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
    conn.execute("DROP TABLE IF EXISTS contract_entries")
    conn.execute("DROP TABLE IF EXISTS test_baseline")
    conn.execute("DROP TABLE IF EXISTS test_design_entries")
    conn.execute("DROP TABLE IF EXISTS design_review")
    conn.executescript(LEGACY_CONTRACT_ENTRIES_SCHEMA)
    conn.execute(
        "INSERT INTO contract_entries (contract_type, source_path, raw_spec) VALUES (?, ?, ?)",
        ("cli-contract", "docs/features/demo/D-API/api.yaml", "{}"),
    )
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (19, '2026-05-12T00:00:00')"
    )
    conn.commit()

    helix_db.migrate(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN "
            "('test_baseline', 'test_design_entries', 'design_review')"
        ).fetchall()
    }
    contract_columns = {
        row[1]: row[4] for row in conn.execute("PRAGMA table_info(contract_entries)").fetchall()
    }
    version_rows = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")]
    design_level = conn.execute("SELECT design_level FROM contract_entries").fetchone()[0]
    conn.close()

    assert tables == {"test_baseline", "test_design_entries", "design_review"}
    assert contract_columns["design_level"] == "'detailed'"
    assert version_rows == list(range(19, helix_db.CURRENT_SCHEMA_VERSION + 1))
    assert design_level == "detailed"


def test_migrate_v19_to_v20_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    helix_db.init_db(str(db_path))
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        version_rows = conn.execute(
            "SELECT version FROM schema_version WHERE version = 20"
        ).fetchall()
        contract_columns = [row["name"] for row in conn.execute("PRAGMA table_info(contract_entries)").fetchall()]
        baseline_columns = [row["name"] for row in conn.execute("PRAGMA table_info(test_baseline)").fetchall()]
    finally:
        conn.close()

    assert len(version_rows) == 1
    assert contract_columns.count("design_level") == 1
    assert baseline_columns.count("code_entry_id") == 1
    assert baseline_columns.count("test_design_id") == 1
