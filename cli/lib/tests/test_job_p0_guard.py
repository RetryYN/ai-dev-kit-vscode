import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import job_p0_guard as guard


def test_authorization_explicit_consent() -> None:
    ok, messages = guard.validate_authorization(
        "consent:2026-05-21T00:00:00Z",
        "PLAN-091",
        "explicit_consent",
        "P3",
    )
    assert ok is True
    assert messages == []


def test_authorization_wbs_match() -> None:
    ok, messages = guard.validate_authorization(
        "wbs:WBS-091-P0",
        "PLAN-091",
        "current_wbs_match",
        "P2",
    )
    assert ok is True
    assert messages == []


def test_authorization_handover_match() -> None:
    ok, messages = guard.validate_authorization(
        "handover:CURRENT.json#next_action[2]",
        "PLAN-091",
        "handover_next_action_match",
        "P3",
    )
    assert ok is True
    assert messages == []


def test_authorization_none_warn() -> None:
    ok, messages = guard.validate_authorization(None, None, None, "P1")
    assert ok is True
    assert "authorization_ref is required" in messages
    assert "source_plan_id is required" in messages
    assert any("authorized_by must include one of" in message for message in messages)


def test_authorization_all_three_pass() -> None:
    ok, messages = guard.validate_authorization(
        "consent:all-three",
        "PLAN-091",
        '["explicit_consent", "wbs_match", "handover_match"]',
        "P3",
    )
    assert ok is True
    assert messages == []


def test_authorization_requires_source_plan_id_from_p2() -> None:
    ok, messages = guard.validate_authorization(
        "consent:missing-plan",
        None,
        "explicit_consent",
        "P2",
    )
    assert ok is False
    assert messages == ["source_plan_id is required"]


def test_authorization_rejects_unknown_authorized_by_values() -> None:
    ok, messages = guard.validate_authorization(
        "consent:unknown-role",
        "PLAN-091",
        "unknown_value",
        "P3",
    )
    assert ok is False
    assert any("authorized_by contains unknown values" in message for message in messages)
    assert any("authorized_by must include one of" in message for message in messages)
