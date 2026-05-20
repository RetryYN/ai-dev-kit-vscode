from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from curator.escalation_matrix import evaluate_escalation


def test_evaluate_zero() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-010 (違反 0 件は advisory warn に留める)"""
    assert evaluate_escalation("PLAN-093:missing-artifact", violation_count=0, days_active=0) == "warn"


def test_evaluate_low_warn() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-011 (軽微な再発は warn を維持する)"""
    assert evaluate_escalation("PLAN-093:missing-artifact", violation_count=2, days_active=10) == "warn"


def test_evaluate_p1_advisory_warn_only() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-012 (P1 advisory は warn のみに固定する)"""
    assert evaluate_escalation("P1:advisory", violation_count=8, days_active=120) == "warn"


def test_evaluate_error_and_fail_close_thresholds() -> None:
    """DoD 検証: PLAN-093-test-design.md U-093-013 (閾値到達で error / fail-close へ昇格する)"""
    assert evaluate_escalation("PLAN-093:missing-artifact", violation_count=3, days_active=5) == "error"
    assert evaluate_escalation("PLAN-093:missing-artifact", violation_count=5, days_active=5) == "fail-close"

