"""v33 -> v34 migration: todo_entries additive schema.

Design references:
- docs/plans/PLAN-088-todowrite-agent-slot-framework.md §4
- cli/lib/helix_db.py
"""

from sqlite3 import Connection

CURRENT_SCHEMA_VERSION = 34

TODO_ENTRIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS todo_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    agent_type TEXT NOT NULL CHECK (length(trim(agent_type)) > 0),
    normalized_agent_type TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('pending', 'in_progress', 'blocked', 'done', 'cancelled')),
    blocked_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    parallel_slot INTEGER,
    owner TEXT,
    metadata_json TEXT DEFAULT '{}'
)
"""

TODO_ENTRIES_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_todo_entries_agent_state "
    "ON todo_entries(agent_type, state);",
    "CREATE INDEX IF NOT EXISTS ix_todo_entries_updated "
    "ON todo_entries(updated_at);",
)


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


def ensure_v34_additive_schema(conn: Connection) -> None:
    """Ensure todo_entries exists even when schema_version already says 34."""
    conn.executescript(TODO_ENTRIES_SCHEMA)
    for statement in TODO_ENTRIES_INDEXES:
        conn.execute(statement)


def migrate_v33_to_v34(conn: Connection) -> None:
    """Apply the additive v34 migration for helix.db."""
    _ensure_schema_version_table(conn)
    ensure_v34_additive_schema(conn)

    if _current_version(conn) < CURRENT_SCHEMA_VERSION:
        _record_schema_version(conn)

    conn.commit()
