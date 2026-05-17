"""Unit tests for cli/lib/cutover_orchestrator.py.

設計参照:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-cutover-gate5.md
- docs/v2/L4-test-design/PLAN-084-integration-test-design.md §2.4-2.5
"""

from __future__ import annotations

import pytest

from cli.lib import cutover_orchestrator


# @helix:index id=plan084.cutover-orchestrator.tests domain=cli/lib/tests summary=PLAN-084 gate 5 cutover orchestrator unit tests


def _set_gate5_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cutover_orchestrator,
        "_DUAL_WRITE_HEALTH_PROBE",
        lambda: {
            "healthy": True,
            "source": "dual-write-mismatch-gate",
            "details": "10000 clean writes",
        },
    )
    monkeypatch.setattr(
        cutover_orchestrator,
        "_REPLAY_STATUS_PROBE",
        lambda: {
            "completed": True,
            "source": "shadow-replay-gate",
            "details": "1000 event replay matched",
        },
    )
    monkeypatch.setattr(cutover_orchestrator, "_MISMATCH_COUNT_PROBE", lambda: 0)


def test_cutover_preflight_ready_when_gate5_inputs_are_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: D-API-SEP-cutover-gate5.md CT-001 (preflight は gate 5 条件を集約する)"""
    _set_gate5_ready(monkeypatch)

    result = cutover_orchestrator.cutover_preflight()

    assert result.ready is True
    assert result.blockers == []
    assert result.replay_completed is True
    assert result.dual_write_health["healthy"] is True
    assert result.dual_write_health["mismatch_count"] == 0


def test_cutover_preflight_collects_blockers_when_gate5_is_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: D-API-SEP-cutover-gate5.md CT-002 (blocker は dual-write/replay/mismatch を fail-close する)"""
    monkeypatch.setattr(
        cutover_orchestrator,
        "_DUAL_WRITE_HEALTH_PROBE",
        lambda: {
            "healthy": False,
            "source": "dual-write-mismatch-gate",
            "details": "clean write streak reset",
        },
    )
    monkeypatch.setattr(
        cutover_orchestrator,
        "_REPLAY_STATUS_PROBE",
        lambda: {
            "completed": False,
            "source": "shadow-replay-gate",
            "details": "replay drift detected",
        },
    )
    monkeypatch.setattr(cutover_orchestrator, "_MISMATCH_COUNT_PROBE", lambda: 2)

    result = cutover_orchestrator.cutover_preflight()

    assert result.ready is False
    assert result.blockers == [
        "dual_write_unhealthy",
        "dual_write_mismatch_detected:2",
        "shadow_replay_incomplete",
    ]
    assert result.dual_write_health["mismatch_count"] == 2
    assert result.replay_completed is False


@pytest.mark.parametrize(
    "confirm_token",
    ["", "   ", "APPROVED-2026-05-18", "PO-APPROVED-"],
)
def test_cutover_execute_requires_po_confirmation_token(
    monkeypatch: pytest.MonkeyPatch, confirm_token: str
) -> None:
    """DoD 検証: D-API-SEP-cutover-gate5.md CT-003 (execute は PO 承認 token を必須化する)"""
    _set_gate5_ready(monkeypatch)

    with pytest.raises(ValueError):
        cutover_orchestrator.cutover_execute(confirm_token=confirm_token)


def test_cutover_execute_fail_closes_when_preflight_is_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: D-API-SEP-cutover-gate5.md CT-004 (preflight NG の cutover 実行を禁止する)"""
    hook_called = {"value": False}
    monkeypatch.setattr(
        cutover_orchestrator,
        "_DUAL_WRITE_HEALTH_PROBE",
        lambda: {"healthy": True, "source": "dual-write-mismatch-gate"},
    )
    monkeypatch.setattr(
        cutover_orchestrator,
        "_REPLAY_STATUS_PROBE",
        lambda: {"completed": False, "source": "shadow-replay-gate"},
    )
    monkeypatch.setattr(cutover_orchestrator, "_MISMATCH_COUNT_PROBE", lambda: 0)
    monkeypatch.setattr(
        cutover_orchestrator,
        "_EXECUTE_HOOK",
        lambda token, preflight: hook_called.update(value=True),
    )

    with pytest.raises(RuntimeError, match="cutover_preflight_failed"):
        cutover_orchestrator.cutover_execute(
            confirm_token="PO-APPROVED-2026-05-18"
        )

    assert hook_called["value"] is False


def test_cutover_execute_returns_manual_carry_payload_when_hook_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: D-API-SEP-cutover-gate5.md CT-005 (コード完成時点では本番 carry 用 payload を返す)"""
    _set_gate5_ready(monkeypatch)
    monkeypatch.setattr(cutover_orchestrator, "_EXECUTE_HOOK", None)

    result = cutover_orchestrator.cutover_execute(
        confirm_token="PO-APPROVED-2026-05-18"
    )

    assert result["status"] == "po_carry_required"
    assert result["executed"] is False
    assert result["confirm_token"] == "PO-APPROVED-2026-05-18"
    assert result["rollback_window_days"] == 7
    assert result["preflight"]["ready"] is True
