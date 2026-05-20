"""v34 -> v35 migration: PLAN registry additive schema.

Design references:
- docs/plans/PLAN-092-posttooluse-plan-auto-register.md §5 / §8
- cli/lib/helix_db.py
"""

from sqlite3 import Connection

CURRENT_SCHEMA_VERSION = 35

PLAN_REGISTRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_registry (
    plan_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    layer TEXT NOT NULL,
    drive TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    size TEXT,
    owner TEXT,
    related_adr TEXT,
    frontmatter_json TEXT NOT NULL,
    doc_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_plan_registry_status ON plan_registry(status);
CREATE INDEX IF NOT EXISTS idx_plan_registry_kind ON plan_registry(kind);
"""

PLAN_DEPENDENCIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    dep_type TEXT NOT NULL,
    dep_plan_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    UNIQUE (plan_id, dep_type, dep_plan_id)
);
CREATE INDEX IF NOT EXISTS idx_plan_deps_plan_id ON plan_dependencies(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_deps_dep_plan_id ON plan_dependencies(dep_plan_id);
"""

PLAN_AGENT_SLOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_agent_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    role TEXT NOT NULL,
    slot_label TEXT,
    slot_index INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_plan_slots_plan_id ON plan_agent_slots(plan_id);
"""

PLAN_REFERENCES_SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    doc_path TEXT NOT NULL,
    section TEXT,
    ref_type TEXT NOT NULL DEFAULT 'related_docs',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_plan_refs_plan_id ON plan_references(plan_id);
"""

PLAN_GENERATES_SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_generates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    exists_check INTEGER NOT NULL DEFAULT 0,
    last_checked_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    UNIQUE (plan_id, artifact_path)
);
CREATE INDEX IF NOT EXISTS idx_plan_generates_plan_id ON plan_generates(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_generates_artifact ON plan_generates(artifact_path);
"""

SPRINT_PROGRESS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sprint_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    completed_files TEXT,
    blocker_note TEXT,
    session_id TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    UNIQUE (plan_id, sprint_id)
);
CREATE INDEX IF NOT EXISTS idx_sprint_progress_plan_id ON sprint_progress(plan_id);
CREATE INDEX IF NOT EXISTS idx_sprint_progress_status ON sprint_progress(status);
"""

FAILURE_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS failure_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    failure_type TEXT NOT NULL,
    context TEXT,
    plan_id TEXT,
    recovery_plan_id TEXT,
    severity TEXT NOT NULL DEFAULT 'warn',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_failure_log_session ON failure_log(session_id);
CREATE INDEX IF NOT EXISTS idx_failure_log_type ON failure_log(failure_type);
CREATE INDEX IF NOT EXISTS idx_failure_log_created ON failure_log(created_at);
"""

POC_VALIDATION_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS poc_validation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    scrum_type TEXT NOT NULL,
    reverse_type TEXT,
    plan_id TEXT,
    result TEXT NOT NULL,
    evidence TEXT,
    forward_layer TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_poc_validation_hypothesis ON poc_validation_log(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_poc_validation_result ON poc_validation_log(result);
"""

REFACTOR_DEGRADE_PATTERN_SCHEMA = """
CREATE TABLE IF NOT EXISTS refactor_degrade_pattern (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT UNIQUE NOT NULL,
    trigger TEXT NOT NULL,
    description TEXT,
    escalation_level TEXT NOT NULL DEFAULT 'warn',
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    promoted_at TEXT,
    demoted_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_degrade_pattern_id ON refactor_degrade_pattern(pattern_id);
CREATE INDEX IF NOT EXISTS idx_degrade_escalation ON refactor_degrade_pattern(escalation_level);
"""

HOTFIX_INCIDENT_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS hotfix_incident_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT UNIQUE NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    root_cause TEXT,
    recovery_ref TEXT,
    resolved_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_hotfix_incident_id ON hotfix_incident_log(incident_id);
CREATE INDEX IF NOT EXISTS idx_hotfix_severity ON hotfix_incident_log(severity);
"""

SCHEMA_STATEMENTS = (
    PLAN_REGISTRY_SCHEMA,
    PLAN_DEPENDENCIES_SCHEMA,
    PLAN_AGENT_SLOTS_SCHEMA,
    PLAN_REFERENCES_SCHEMA,
    PLAN_GENERATES_SCHEMA,
    SPRINT_PROGRESS_SCHEMA,
    FAILURE_LOG_SCHEMA,
    POC_VALIDATION_LOG_SCHEMA,
    REFACTOR_DEGRADE_PATTERN_SCHEMA,
    HOTFIX_INCIDENT_LOG_SCHEMA,
)

V35_TABLE_NAMES = (
    "plan_registry",
    "plan_dependencies",
    "plan_agent_slots",
    "plan_references",
    "plan_generates",
    "sprint_progress",
    "failure_log",
    "poc_validation_log",
    "refactor_degrade_pattern",
    "hotfix_incident_log",
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


def ensure_v35_additive_schema(conn: Connection) -> None:
    """Ensure PLAN-092 v35 additive tables exist."""
    for statement in SCHEMA_STATEMENTS:
        conn.executescript(statement)


def migrate_v34_to_v35(conn: Connection) -> None:
    """Apply the additive v35 migration for helix.db."""
    _ensure_schema_version_table(conn)
    ensure_v35_additive_schema(conn)

    if _current_version(conn) < CURRENT_SCHEMA_VERSION:
        _record_schema_version(conn)

    conn.commit()
