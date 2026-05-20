"""契約: PLAN-097 §8 §9

Minimal escalation helpers for the three-stage abstraction-layer rollout.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum


class EscalationLevel(str, Enum):
    """Three-step escalation level used by PLAN-097 Sprint .1."""

    WARN = "warn"
    ERROR = "error"
    FAIL_CLOSE = "fail_close"


_SEVERITY_SCORES = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def evaluate(violation_count: int, severity: str, history: Iterable[object]) -> EscalationLevel:
    """Return the current escalation level from count, severity, and prior violations."""
    severity_score = _normalize_severity(severity)
    repeated_violations = _count_repeated_violations(history)

    if violation_count >= 15 or severity_score >= 3 or repeated_violations >= 7:
        return EscalationLevel.FAIL_CLOSE
    if violation_count >= 7 or severity_score >= 2 or repeated_violations >= 3:
        return EscalationLevel.ERROR
    return EscalationLevel.WARN


def promote(current_level: EscalationLevel) -> EscalationLevel:
    """Promote one step and keep the max level unchanged."""
    level = EscalationLevel(current_level)
    if level == EscalationLevel.WARN:
        return EscalationLevel.ERROR
    if level == EscalationLevel.ERROR:
        return EscalationLevel.FAIL_CLOSE
    return EscalationLevel.FAIL_CLOSE


def _normalize_severity(severity: str) -> int:
    return _SEVERITY_SCORES.get(str(severity).strip().lower(), 0)


def _count_repeated_violations(history: Iterable[object]) -> int:
    return sum(_violation_weight(entry) for entry in history)


def _violation_weight(entry: object) -> int:
    if isinstance(entry, bool):
        return int(entry)
    if isinstance(entry, int):
        return 1 if entry > 0 else 0
    if isinstance(entry, Mapping):
        if "violation_count" in entry:
            count = entry["violation_count"]
            return int(count) if isinstance(count, int) and count > 0 else 0
        if "count" in entry:
            count = entry["count"]
            return int(count) if isinstance(count, int) and count > 0 else 0
        if "violated" in entry:
            return int(bool(entry["violated"]))
    return int(bool(entry))


__all__ = ["EscalationLevel", "evaluate", "promote"]
