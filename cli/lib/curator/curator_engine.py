"""契約: PLAN-093 §7

Curator failure_log 集計と refactor_degrade_pattern 登録を担う最小実装。
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import sqlite3

try:
    from .escalation_matrix import evaluate_escalation
except ImportError:  # pragma: no cover
    from escalation_matrix import evaluate_escalation


ESCALATION_THRESHOLD = 3
DEMOTION_STALE_DAYS = 30
ARCHIVE_STALE_DAYS = 90


def analyze_pattern(failure_log_entries: list[dict]) -> dict:
    """Aggregate failure_log entries into one curator pattern summary."""
    if not failure_log_entries:
        return {
            "pattern_id": "global:unclassified",
            "trigger": "unknown",
            "description": "No failure_log entries supplied.",
            "plan_id": None,
            "violation_count": 0,
            "occurrence_count": 0,
            "days_active": 0,
            "escalation_level": "warn",
            "promotion_candidate": False,
            "demotion_candidate": False,
            "archive_candidate": False,
        }

    failure_type = _most_common_text(failure_log_entries, "failure_type", default="unknown")
    plan_id = _most_common_text(failure_log_entries, "plan_id", default=None)
    contexts = [str(entry.get("context") or "").strip() for entry in failure_log_entries if entry.get("context")]
    timestamps = [_parse_timestamp(entry.get("created_at")) for entry in failure_log_entries]
    parsed_timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
    now = datetime.now(UTC)
    oldest_seen = min(parsed_timestamps) if parsed_timestamps else now
    days_active = max((now - oldest_seen).days, 0)
    violation_count = len(failure_log_entries)
    pattern_id = f"{plan_id or 'global'}:{failure_type}"
    escalation_level = evaluate_escalation(pattern_id, violation_count=violation_count, days_active=days_active)

    return {
        "pattern_id": pattern_id,
        "trigger": failure_type,
        "description": contexts[0] if contexts else f"Observed {violation_count} curator failures for {failure_type}.",
        "plan_id": plan_id,
        "violation_count": violation_count,
        "occurrence_count": violation_count,
        "days_active": days_active,
        "escalation_level": escalation_level,
        "promotion_candidate": violation_count >= ESCALATION_THRESHOLD,
        "demotion_candidate": days_active >= DEMOTION_STALE_DAYS and violation_count == 0,
        "archive_candidate": days_active >= ARCHIVE_STALE_DAYS and violation_count == 0,
    }


def register_pattern(conn: sqlite3.Connection, pattern_dict: dict) -> int:
    """Upsert one curator pattern row and return its integer row id."""
    if not isinstance(pattern_dict, dict):
        raise TypeError("pattern_dict must be a dict")

    pattern_id = str(pattern_dict.get("pattern_id") or "").strip()
    if not pattern_id:
        raise ValueError("pattern_dict.pattern_id is required")

    trigger = str(pattern_dict.get("trigger") or pattern_dict.get("failure_type") or "unknown").strip()
    description = pattern_dict.get("description")
    violation_count = max(
        int(pattern_dict.get("occurrence_count") or pattern_dict.get("violation_count") or 0),
        0,
    )
    days_active = max(int(pattern_dict.get("days_active") or 0), 0)
    escalation_level = str(
        pattern_dict.get("escalation_level")
        or evaluate_escalation(pattern_id, violation_count=violation_count, days_active=days_active)
    ).strip()
    now = _sqlite_now()
    promoted_at = now if escalation_level in {"error", "fail-close"} else None
    demoted_at = now if pattern_dict.get("demotion_candidate") or pattern_dict.get("archive_candidate") else None

    conn.execute(
        """
        INSERT INTO refactor_degrade_pattern (
            pattern_id,
            trigger,
            description,
            escalation_level,
            occurrence_count,
            promoted_at,
            demoted_at,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(pattern_id) DO UPDATE SET
            trigger = excluded.trigger,
            description = excluded.description,
            escalation_level = excluded.escalation_level,
            occurrence_count = excluded.occurrence_count,
            promoted_at = COALESCE(excluded.promoted_at, refactor_degrade_pattern.promoted_at),
            demoted_at = COALESCE(excluded.demoted_at, refactor_degrade_pattern.demoted_at),
            updated_at = excluded.updated_at
        """,
        (
            pattern_id,
            trigger,
            description,
            escalation_level,
            violation_count,
            promoted_at,
            demoted_at,
            now,
            now,
        ),
    )
    row = conn.execute(
        "SELECT id FROM refactor_degrade_pattern WHERE pattern_id = ?",
        (pattern_id,),
    ).fetchone()
    if row is None:
        raise sqlite3.IntegrityError(f"failed to register pattern: {pattern_id}")
    return int(row[0])


def _most_common_text(entries: list[dict], key: str, default: str | None) -> str | None:
    values = [str(entry.get(key) or "").strip() for entry in entries if str(entry.get(key) or "").strip()]
    if not values:
        return default
    return Counter(values).most_common(1)[0][0]


def _parse_timestamp(value: object) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    for candidate in (normalized, normalized.replace(" ", "T")):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _sqlite_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = ["analyze_pattern", "register_pattern"]

