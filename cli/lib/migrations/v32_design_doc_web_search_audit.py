"""v31 -> v32 migration: detector_runs + design_doc_web_search_audit tables.

Design references:
- docs/plans/PLAN-087-design-doc-web-search-guardrail.md §4 Phase 3
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

DESIGN_DOC_WEB_SEARCH_AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS design_doc_web_search_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT,
    adr_id TEXT,
    hook_session_id TEXT NOT NULL,
    web_search_executed INTEGER NOT NULL CHECK (web_search_executed IN (0, 1)),
    oss_search_executed INTEGER NOT NULL CHECK (oss_search_executed IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (plan_id IS NOT NULL AND length(trim(plan_id)) > 0)
        OR (adr_id IS NOT NULL AND length(trim(adr_id)) > 0)
    )
)
"""

DESIGN_DOC_WEB_SEARCH_AUDIT_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_design_doc_web_search_audit_plan_created "
    "ON design_doc_web_search_audit(plan_id, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_design_doc_web_search_audit_adr_created "
    "ON design_doc_web_search_audit(adr_id, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_design_doc_web_search_audit_session "
    "ON design_doc_web_search_audit(hook_session_id, created_at DESC);",
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


def ensure_v32_additive_schema(conn: Connection) -> None:
    """Ensure v32 additive tables exist even when schema_version already says 32."""
    conn.executescript(DETECTOR_RUNS_SCHEMA)
    conn.executescript(DESIGN_DOC_WEB_SEARCH_AUDIT_SCHEMA)
    for statement in DESIGN_DOC_WEB_SEARCH_AUDIT_INDEXES:
        conn.execute(statement)


# @helix:index id=migrations.v32-design-doc-web-search-audit.migrate-v31-to-v32 domain=cli/lib/migrations summary=v31→v32 migration、detector_runs と design_doc_web_search_audit を追加する
def migrate_v31_to_v32(conn: Connection) -> None:
    """Apply the additive v32 migration for backend.db."""
    _ensure_schema_version_table(conn)
    ensure_v32_additive_schema(conn)

    if _current_version(conn) < CURRENT_SCHEMA_VERSION:
        _record_schema_version(conn)

    conn.commit()
