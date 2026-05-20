"""契約: PLAN-097 §8 §11 + PLAN-093 §7

Curator の failure 集計と escalation persistence を接続する薄い統合層。
"""

from __future__ import annotations

try:
    import helix_db
    from curator.curator_engine import analyze_pattern, register_pattern
    from curator.escalation_matrix import evaluate_escalation
except ImportError:  # pragma: no cover
    from . import helix_db
    from .curator.curator_engine import analyze_pattern, register_pattern
    from .curator.escalation_matrix import evaluate_escalation


def integrate_with_curator(failure_log_entries: list[dict]) -> dict:
    """Analyze failure entries, recalculate escalation, and upsert the curator row."""
    if not isinstance(failure_log_entries, list):
        raise TypeError("failure_log_entries must be a list[dict]")
    if any(not isinstance(entry, dict) for entry in failure_log_entries):
        raise TypeError("failure_log_entries must contain only dict items")

    pattern = analyze_pattern(failure_log_entries)
    escalation_level = evaluate_escalation(
        str(pattern.get("pattern_id") or ""),
        violation_count=int(pattern.get("violation_count") or pattern.get("occurrence_count") or 0),
        days_active=int(pattern.get("days_active") or 0),
    )
    persisted_pattern = dict(pattern)
    persisted_pattern["escalation_level"] = escalation_level

    with helix_db._write_connection(None) as conn:
        _ensure_refactor_degrade_pattern_table(conn)
        row_id = register_pattern(conn, persisted_pattern)

    result = dict(persisted_pattern)
    result["row_id"] = row_id
    result["db_path"] = helix_db.resolve_default_db_path()
    return result


__all__ = ["integrate_with_curator"]


def _ensure_refactor_degrade_pattern_table(conn) -> None:
    conn.executescript(
        """
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
        CREATE INDEX IF NOT EXISTS idx_degrade_pattern_id
            ON refactor_degrade_pattern(pattern_id);
        CREATE INDEX IF NOT EXISTS idx_degrade_escalation
            ON refactor_degrade_pattern(escalation_level);
        """
    )
