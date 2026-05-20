from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import demotion_checker
from escalation_engine import EscalationLevel


def test_demote_after_30_days_zero_violation() -> None:
    """DoD 検証: PLAN-097 §12 U-097-015 (30 日間違反ゼロなら降格候補になる)"""
    eligible = demotion_checker.check_demotion_eligibility(
        rule_id="RULE-097",
        days=30,
        violation_history=[{"rule_id": "RULE-097", "days_ago": 30, "violated": False}],
    )

    assert eligible is True
    assert demotion_checker.demote(EscalationLevel.ERROR) is EscalationLevel.WARN


def test_no_demote_with_recent_violation() -> None:
    """DoD 検証: PLAN-097 §12 U-097-014 (直近違反がある場合は降格しない)"""
    eligible = demotion_checker.check_demotion_eligibility(
        rule_id="RULE-097",
        days=30,
        violation_history=[{"rule_id": "RULE-097", "days_ago": 2, "violated": True}],
    )

    assert eligible is False


def test_demote_chain() -> None:
    """DoD 検証: PLAN-097 §12 U-097-015 (降格は FAIL_CLOSE → ERROR → WARN の順で進む)"""
    assert demotion_checker.demote(EscalationLevel.FAIL_CLOSE) is EscalationLevel.ERROR
    assert demotion_checker.demote(EscalationLevel.ERROR) is EscalationLevel.WARN
    assert demotion_checker.demote(EscalationLevel.WARN) is EscalationLevel.WARN
