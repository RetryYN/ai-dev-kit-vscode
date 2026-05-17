"""v30 -> v31 migration: additive separation scaffolding.

Sprint 4.A.1 scope:
- Add ``event_envelope`` and ``projection_state`` to legacy ``helix.db``.
- Keep the migration idempotent.
- Preserve all v30 tables unchanged.
- Record schema version 31.

Design references:
- D-DB-SEP-draft §3/§4/§6
"""

from pathlib import Path
from sqlite3 import Connection

CURRENT_SCHEMA_VERSION = 31

EVENT_ENVELOPE_SCHEMA = """
CREATE TABLE IF NOT EXISTS event_envelope (
    event_id        TEXT NOT NULL UNIQUE,
    aggregate_id    TEXT NOT NULL CHECK(length(aggregate_id) > 0),
    aggregate_type  TEXT NOT NULL CHECK(length(aggregate_type) > 0),
    db_name         TEXT NOT NULL CHECK (db_name IN ('orchestration','vmodel','scrum')),
    event_type      TEXT NOT NULL CHECK(length(event_type) > 0),
    payload         JSON NOT NULL,
    correlation_id  TEXT NOT NULL CHECK(length(correlation_id) > 0),
    occurred_at     TEXT NOT NULL CHECK(length(occurred_at) > 0),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (db_name, event_id)
);
"""

PROJECTION_STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS projection_state (
    projector_id            TEXT NOT NULL,
    db_name                 TEXT NOT NULL,
    last_processed_event_id TEXT NOT NULL,
    snapshot                JSON,
    updated_at              TEXT NOT NULL,
    PRIMARY KEY (projector_id, db_name)
);
"""

EVENT_ENVELOPE_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_event_envelope_occurred_at ON event_envelope(db_name, occurred_at);",
    "CREATE INDEX IF NOT EXISTS idx_event_envelope_correlation ON event_envelope(correlation_id);",
    "CREATE INDEX IF NOT EXISTS idx_event_envelope_aggregate ON event_envelope(aggregate_type, aggregate_id);",
)

PLANNED_DB_FILENAMES: dict[str, str] = {
    "orchestration": "orchestration.db",
    "vmodel": "vmodel.db",
    "scrum": "scrum.db",
    "plan": "plan.db",
    "backend": "backend.db",
    "frontend": "frontend.db",
}


def _ensure_event_tables(conn: Connection) -> None:
    conn.executescript(EVENT_ENVELOPE_SCHEMA)
    conn.executescript(PROJECTION_STATE_SCHEMA)
    for statement in EVENT_ENVELOPE_INDEXES:
        conn.execute(statement)


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


def _planned_db_paths(base_dir: str | Path) -> dict[str, str]:
    """Return the Phase 4.A.2 target db layout without creating files yet."""
    root = Path(base_dir)
    return {
        db_name: str(root / filename)
        for db_name, filename in PLANNED_DB_FILENAMES.items()
    }


def _planned_db_names() -> tuple[str, ...]:
    return tuple(PLANNED_DB_FILENAMES)


# @helix:index id=migrations.v31-db-separation.planned-split-db-paths domain=cli/lib/migrations summary=Phase 4.A.2 で作成予定の 6 db path を返す
def planned_split_db_paths(base_dir: str | Path) -> dict[str, str]:
    """Expose the Phase 4.A.2 file layout for callers that need dry-run paths."""
    return _planned_db_paths(base_dir)


# @helix:index id=migrations.v31-db-separation.migrate-v30-to-v31 domain=cli/lib/migrations summary=v30→v31 migration、event_envelope + projection_state 追加 (gate 1 skeleton)
def migrate_v30_to_v31(conn: Connection) -> None:
    """Apply the additive portion of the v31 migration.

    The function is intentionally conservative: it only installs the two new
    tables plus their indexes and records version 31. Physical 6-db creation,
    dual-write verification, replay, and cutover remain later sprint work.
    """
    _ensure_schema_version_table(conn)
    if _current_version(conn) >= CURRENT_SCHEMA_VERSION:
        _ensure_event_tables(conn)
        conn.commit()
        return

    _ensure_event_tables(conn)
    _record_schema_version(conn)
    conn.commit()
