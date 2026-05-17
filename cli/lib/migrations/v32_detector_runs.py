"""v31 -> v32 migration: detector_runs table for backend dual-write checks.

Design references:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md §C
- cli/lib/detectors/base.py
"""

from sqlite3 import Connection

CURRENT_SCHEMA_VERSION = 32

DETECTOR_RUNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS detector_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TEXT NOT NULL,
    axis_id TEXT NOT NULL,
    detector_name TEXT NOT NULL,
    phase_gate TEXT,
    verdict TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    cost_ms INTEGER NOT NULL,
    raw_json TEXT NOT NULL,
    config_json TEXT NOT NULL,
    command TEXT NOT NULL,
    db_path TEXT NOT NULL
)
"""


def _ensure_schema_version_table(conn: Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _record_schema_version(conn: Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
        (CURRENT_SCHEMA_VERSION,),
    )


def _current_version(conn: Connection) -> int:
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return int(row[0] or 0)


def _ensure_detector_runs_table(conn: Connection) -> None:
    conn.executescript(DETECTOR_RUNS_SCHEMA)


# @helix:index id=migrations.v32-detector-runs.migrate-v31-to-v32 domain=cli/lib/migrations summary=v31→v32 migration、backend detector_runs table を追加する
def migrate_v31_to_v32(conn: Connection) -> None:
    """Apply the additive detector_runs migration for backend.db."""
    _ensure_schema_version_table(conn)
    _ensure_detector_runs_table(conn)

    if _current_version(conn) < CURRENT_SCHEMA_VERSION:
        _record_schema_version(conn)

    conn.commit()
