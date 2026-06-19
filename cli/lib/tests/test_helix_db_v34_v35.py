"""Migration tests for cli/lib/migrations/v34_todo_entries.py and v35_plan_registry.py."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from cli.lib import helix_db
from cli.lib.migrations import (
    v31_db_separation,
    v32_design_doc_web_search_audit,
    v33_gate_audit_metrics,
    v34_todo_entries,
    v35_plan_registry,
)


def _build_v30_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (30, '2026-05-22T00:00:00+00:00')"
    )
    conn.commit()
    return conn


def _build_v33_db(db_path: Path) -> sqlite3.Connection:
    conn = _build_v30_db(db_path)
    v31_db_separation.migrate_v30_to_v31(conn)
    v32_design_doc_web_search_audit.migrate_v31_to_v32(conn)
    v33_gate_audit_metrics.migrate_v32_to_v33(conn)
    return conn


def test_v34_creates_todo_entries_table(tmp_path: Path) -> None:
    """DoD 検証: PLAN-100-WAVE-3AB-V2 T-V34-001 (v33→v34 で todo_entries が作成される)"""
    conn = _build_v33_db(tmp_path / "legacy-v33.db")
    try:
        v34_todo_entries.migrate_v33_to_v34(conn)
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(todo_entries)").fetchall()]
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()]
    finally:
        conn.close()

    assert columns == [
        "id",
        "session_id",
        "content",
        "agent_type",
        "normalized_agent_type",
        "state",
        "blocked_by",
        "created_at",
        "updated_at",
        "parallel_slot",
        "owner",
        "metadata_json",
    ]
    assert versions[-4:] == [31, 32, 33, 34]


# IT-IF-04
def test_v35_creates_10_tables(tmp_path: Path) -> None:
    """DoD 検証: PLAN-100-WAVE-3AB-V2 T-V35-001 (v34→v35 で 10 table が作成される)"""
    conn = _build_v33_db(tmp_path / "legacy-v34.db")
    try:
        v34_todo_entries.migrate_v33_to_v34(conn)
        v35_plan_registry.migrate_v34_to_v35(conn)
        created_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()]
    finally:
        conn.close()

    assert set(v35_plan_registry.V35_TABLE_NAMES) <= created_tables
    assert versions[-5:] == [31, 32, 33, 34, 35]


# IT-MOD-04
def test_full_chain_to_latest(tmp_path: Path) -> None:
    """DoD 検証: PLAN-100-WAVE-3AB-V2 T-CHAIN-001 (fresh DB を migrate すると最新 (=CURRENT_SCHEMA_VERSION) まで到達する)

    Note: PLAN-156 Sprint .2 で v36 (workspace_registry) を追加したため、最新版到達値は CURRENT_SCHEMA_VERSION
    を正本にして比較する。v34→v35 表面の検証は test_v35_creates_10_tables を参照。
    """
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        todo_entries_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='todo_entries'"
        ).fetchone()
        created_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    finally:
        conn.close()

    assert max_version == helix_db.CURRENT_SCHEMA_VERSION
    assert todo_entries_exists is not None
    assert set(v35_plan_registry.V35_TABLE_NAMES) <= created_tables


# IT-IP-04
def test_idempotent(tmp_path: Path) -> None:
    """DoD 検証: PLAN-100-WAVE-3AB-V2 T-CHAIN-002 (migrate の再実行で schema_version は重複しない)"""
    conn = _build_v33_db(tmp_path / "v35-idempotent.db")
    try:
        helix_db.migrate(conn)
        helix_db.migrate(conn)
        v34_rows = conn.execute("SELECT version FROM schema_version WHERE version = 34").fetchall()
        v35_rows = conn.execute("SELECT version FROM schema_version WHERE version = 35").fetchall()
        created_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    finally:
        conn.close()

    assert len(v34_rows) == 1
    assert len(v35_rows) == 1
    assert "todo_entries" in created_tables
    assert set(v35_plan_registry.V35_TABLE_NAMES) <= created_tables
