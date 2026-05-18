"""v32 -> v33 migration: gate_audit_metrics table.

Design references:
- docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md §5 Phase 2
- cli/helix-gate
"""

from sqlite3 import Connection

CURRENT_SCHEMA_VERSION = 33

GATE_AUDIT_METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS gate_audit_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_name TEXT NOT NULL CHECK (gate_name IN ('G2', 'G3')),
    plan_id TEXT NOT NULL CHECK (length(trim(plan_id)) > 0),
    advisory_result TEXT NOT NULL CHECK (advisory_result IN ('pass', 'warn', 'skip')),
    bypass_used INTEGER NOT NULL CHECK (bypass_used IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

GATE_AUDIT_METRICS_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_gate_audit_metrics_plan_created "
    "ON gate_audit_metrics(plan_id, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_gate_audit_metrics_gate_created "
    "ON gate_audit_metrics(gate_name, created_at DESC);",
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


def ensure_v33_additive_schema(conn: Connection) -> None:
    """Ensure gate_audit_metrics exists even when schema_version already says 33."""
    conn.executescript(GATE_AUDIT_METRICS_SCHEMA)
    for statement in GATE_AUDIT_METRICS_INDEXES:
        conn.execute(statement)


# @helix:index id=migrations.v33-gate-audit-metrics.migrate-v32-to-v33 domain=cli/lib/migrations summary=v32→v33 migration、gate_audit_metrics を追加する
def migrate_v32_to_v33(conn: Connection) -> None:
    """Apply the additive v33 migration for helix.db."""
    _ensure_schema_version_table(conn)
    ensure_v33_additive_schema(conn)

    if _current_version(conn) < CURRENT_SCHEMA_VERSION:
        _record_schema_version(conn)

    conn.commit()
