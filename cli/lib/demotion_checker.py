"""契約: PLAN-097 §10

Minimal demotion helpers for the three-stage abstraction-layer rollout.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

try:
    from escalation_engine import EscalationLevel
except ImportError:
    from cli.lib.escalation_engine import EscalationLevel

DEMOTION_WINDOW_DAYS = 30


def check_demotion_eligibility(rule_id: str, days: int, violation_history: Iterable[object]) -> bool:
    """Return True when the rule stayed unused or violation-free for the full window."""
    if days < DEMOTION_WINDOW_DAYS:
        return False

    for entry in violation_history:
        if not _matches_rule(entry, rule_id):
            continue
        if _days_ago(entry) > days:
            continue
        if _has_violation(entry):
            return False
    return True


def demote(current_level: EscalationLevel) -> EscalationLevel:
    """Demote one step and keep the minimum level unchanged."""
    level = EscalationLevel(current_level)
    if level == EscalationLevel.FAIL_CLOSE:
        return EscalationLevel.ERROR
    if level == EscalationLevel.ERROR:
        return EscalationLevel.WARN
    return EscalationLevel.WARN


def _matches_rule(entry: object, rule_id: str) -> bool:
    if not isinstance(entry, Mapping):
        return True
    entry_rule_id = entry.get("rule_id")
    return entry_rule_id is None or entry_rule_id == rule_id


def _days_ago(entry: object) -> int:
    if not isinstance(entry, Mapping):
        return 0
    for key in ("days_ago", "days_since"):
        value = entry.get(key)
        if isinstance(value, int):
            return value
    return 0


def _has_violation(entry: object) -> bool:
    if isinstance(entry, bool):
        return entry
    if isinstance(entry, int):
        return entry > 0
    if isinstance(entry, Mapping):
        if "violated" in entry:
            return bool(entry["violated"])
        for key in ("violation_count", "count"):
            value = entry.get(key)
            if isinstance(value, int):
                return value > 0
        return False
    return bool(entry)


__all__ = ["DEMOTION_WINDOW_DAYS", "check_demotion_eligibility", "demote"]
