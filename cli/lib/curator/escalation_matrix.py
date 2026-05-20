"""契約: PLAN-093 §7

Curator pattern の violation 強度を HELIX の warn / error / fail-close へ正規化する。
"""

from __future__ import annotations


ERROR_VIOLATION_THRESHOLD = 3
FAIL_CLOSE_VIOLATION_THRESHOLD = 5
ERROR_STALE_DAYS = 30
FAIL_CLOSE_STALE_DAYS = 90


def evaluate_escalation(pattern_id: str, violation_count: int, days_active: int) -> str:
    """Return the escalation level for a curator pattern."""
    normalized_pattern_id = str(pattern_id).strip().upper()
    normalized_count = max(int(violation_count), 0)
    normalized_days = max(int(days_active), 0)

    # PLAN-093 Phase 1 は advisory から導入するため、P1 系は warn に固定する。
    if normalized_pattern_id.startswith("P1"):
        return "warn"
    if normalized_count <= 0:
        return "warn"
    if normalized_count >= FAIL_CLOSE_VIOLATION_THRESHOLD or normalized_days >= FAIL_CLOSE_STALE_DAYS:
        return "fail-close"
    if normalized_count >= ERROR_VIOLATION_THRESHOLD or normalized_days >= ERROR_STALE_DAYS:
        return "error"
    return "warn"


__all__ = ["evaluate_escalation"]

