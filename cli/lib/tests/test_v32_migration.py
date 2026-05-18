"""Migration tests for cli/lib/migrations/v32_detector_runs.py.

設計参照:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md §C
- cli/lib/migrations/v31_db_separation.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from cli.lib import helix_db
from cli.lib.migrations import v31_db_separation, v32_detector_runs


def _build_v30_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (30, '2026-05-18T00:00:00+00:00')"
    )
    conn.commit()
    return conn


# @helix:index id=plan084.v32-migration.tests domain=cli/lib/tests summary=PLAN-084 detector_runs migration tests
def test_migrate_v31_to_v32_adds_detector_runs_and_records_schema_version(tmp_path: Path) -> None:
    """DoD 検証: PLAN-084 Phase 4.B.6 M-V32-001 (v31→v32 で detector_runs と version 32 が入る)"""
    conn = _build_v30_db(tmp_path / "legacy-v30.db")
    try:
        v31_db_separation.migrate_v30_to_v31(conn)
        v32_detector_runs.migrate_v31_to_v32(conn)
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(detector_runs)").fetchall()]
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()]
    finally:
        conn.close()

    assert columns == [
        "run_id",
        "recorded_at",
        "axis_id",
        "detector_name",
        "phase_gate",
        "verdict",
        "findings_json",
        "cost_ms",
        "raw_json",
        "config_json",
        "command",
        "db_path",
    ]
    assert 32 in versions and 31 in versions


def test_migrate_v31_to_v32_is_idempotent(tmp_path: Path) -> None:
    """DoD 検証: PLAN-084 Phase 4.B.6 M-V32-002 (v32 migration は再実行しても重複しない)"""
    conn = _build_v30_db(tmp_path / "v32-idempotent.db")
    try:
        v31_db_separation.migrate_v30_to_v31(conn)
        v32_detector_runs.migrate_v31_to_v32(conn)
        v32_detector_runs.migrate_v31_to_v32(conn)
        version_rows = conn.execute("SELECT version FROM schema_version WHERE version = 32").fetchall()
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(detector_runs)").fetchall()]
    finally:
        conn.close()

    assert len(version_rows) == 1
    assert columns.count("run_id") == 1
    assert columns.count("raw_json") == 1


def test_init_db_reaches_schema_version_32_and_creates_detector_runs(tmp_path: Path) -> None:
    """DoD 検証: PLAN-084 Phase 4.B.6 M-V32-003 (helix_db.init_db でも v32 まで到達する)"""
    db_path = tmp_path / "helix.db"

    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        detector_runs_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='detector_runs'"
        ).fetchone()
    finally:
        conn.close()

    assert max_version >= 32
    assert detector_runs_exists is not None


def test_current_schema_version_is_at_least_32() -> None:
    assert helix_db.CURRENT_SCHEMA_VERSION >= 32
