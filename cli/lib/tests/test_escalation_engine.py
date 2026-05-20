from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import escalation_engine


def test_evaluate_warn() -> None:
    """DoD 検証: PLAN-097 §12 U-097-001 (閾値未満では WARN を返す)"""
    level = escalation_engine.evaluate(violation_count=2, severity="low", history=[])

    assert level is escalation_engine.EscalationLevel.WARN


def test_evaluate_error() -> None:
    """DoD 検証: PLAN-097 §12 U-097-003 (中段閾値到達で ERROR に昇格する)"""
    level = escalation_engine.evaluate(
        violation_count=7,
        severity="medium",
        history=[{"violation_count": 1}] * 3,
    )

    assert level is escalation_engine.EscalationLevel.ERROR


def test_evaluate_fail_close() -> None:
    """DoD 検証: PLAN-097 §12 U-097-004 (上段閾値到達で FAIL_CLOSE に昇格する)"""
    level = escalation_engine.evaluate(
        violation_count=15,
        severity="critical",
        history=[{"violated": True}] * 7,
    )

    assert level is escalation_engine.EscalationLevel.FAIL_CLOSE


def test_promote_warn_to_error() -> None:
    """DoD 検証: PLAN-097 §12 U-097-002 (WARN から 1 段階昇格する)"""
    assert escalation_engine.promote(escalation_engine.EscalationLevel.WARN) is escalation_engine.EscalationLevel.ERROR


def test_promote_error_to_fail_close() -> None:
    """DoD 検証: PLAN-097 §12 U-097-003 (ERROR から FAIL_CLOSE へ昇格する)"""
    assert escalation_engine.promote(escalation_engine.EscalationLevel.ERROR) is escalation_engine.EscalationLevel.FAIL_CLOSE


def test_promote_at_max_no_change() -> None:
    """DoD 検証: PLAN-097 §12 U-097-004 (最大レベルでは昇格しない)"""
    assert escalation_engine.promote(escalation_engine.EscalationLevel.FAIL_CLOSE) is escalation_engine.EscalationLevel.FAIL_CLOSE
