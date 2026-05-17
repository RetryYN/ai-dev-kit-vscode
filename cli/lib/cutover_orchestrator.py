"""Cutover gate 5 orchestration helpers for PLAN-084 Phase 4.C.

Design references:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-cutover-gate5.md
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md
- docs/adr/ADR-018-db-separation-and-event-sourcing.md §Decision.5
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable

_CONFIRM_TOKEN_PREFIX = "PO-APPROVED-"
_ROLLBACK_WINDOW_DAYS = 7


def _default_dual_write_health_probe() -> dict[str, Any]:
    return {
        "healthy": False,
        "source": "unconfigured",
        "details": "dual-write health probe is not wired",
    }


def _default_replay_status_probe() -> dict[str, Any]:
    return {
        "completed": False,
        "source": "unconfigured",
        "details": "shadow replay probe is not wired",
    }


def _default_mismatch_count_probe() -> int | None:
    return None


_DUAL_WRITE_HEALTH_PROBE: Callable[[], dict[str, Any]] = (
    _default_dual_write_health_probe
)
_REPLAY_STATUS_PROBE: Callable[[], dict[str, Any]] = _default_replay_status_probe
_MISMATCH_COUNT_PROBE: Callable[[], int | None] = _default_mismatch_count_probe
_EXECUTE_HOOK: Callable[[str, CutoverPreflightResult], dict[str, Any]] | None = None


@dataclass(frozen=True)
class CutoverPreflightResult:
    ready: bool
    blockers: list[str]
    dual_write_health: dict[str, Any]
    replay_completed: bool


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_mismatch_count(raw_count: int | None) -> int | None:
    if raw_count is None:
        return None
    if raw_count < 0:
        raise ValueError("mismatch_count must be >= 0")
    return raw_count


def _validate_confirm_token(confirm_token: str) -> str:
    token = confirm_token.strip()
    if not token:
        raise ValueError("confirm_token is required")
    if not token.startswith(_CONFIRM_TOKEN_PREFIX):
        raise ValueError(
            "confirm_token must start with 'PO-APPROVED-'"
        )
    if token == _CONFIRM_TOKEN_PREFIX:
        raise ValueError("confirm_token must include an approval suffix")
    return token


# @helix:index id=cutover-orchestrator.preflight domain=cli/lib summary=gate 5 cutover preflight 判定
def cutover_preflight() -> CutoverPreflightResult:
    """cutover 実行前の preflight check (gate 5 判定)."""

    dual_write_health = dict(_DUAL_WRITE_HEALTH_PROBE())
    replay_status = dict(_REPLAY_STATUS_PROBE())
    mismatch_count = _normalize_mismatch_count(_MISMATCH_COUNT_PROBE())

    dual_write_health["mismatch_count"] = mismatch_count
    dual_write_health.setdefault("checked_at", _utc_now())

    blockers: list[str] = []
    if dual_write_health.get("healthy") is not True:
        blockers.append("dual_write_unhealthy")

    if mismatch_count is None:
        blockers.append("dual_write_mismatch_count_unavailable")
    elif mismatch_count != 0:
        blockers.append(f"dual_write_mismatch_detected:{mismatch_count}")

    replay_completed = replay_status.get("completed") is True
    dual_write_health["replay_source"] = replay_status.get("source", "unknown")
    if not replay_completed:
        blockers.append("shadow_replay_incomplete")

    return CutoverPreflightResult(
        ready=not blockers,
        blockers=blockers,
        dual_write_health=dual_write_health,
        replay_completed=replay_completed,
    )


# @helix:index id=cutover-orchestrator.execute domain=cli/lib summary=PO 承認 token 付き gate 5 cutover 実行入口
def cutover_execute(*, confirm_token: str) -> dict[str, Any]:
    """実 cutover 実行 (PO 承認 token 必須、本実装は code 完成のみ、実行は本番で PO carry)."""

    token = _validate_confirm_token(confirm_token)
    preflight = cutover_preflight()
    if not preflight.ready:
        raise RuntimeError(
            "cutover_preflight_failed: " + ", ".join(preflight.blockers)
        )

    result = {
        "status": "po_carry_required",
        "executed": False,
        "confirm_token": token,
        "approved_at": _utc_now(),
        "rollback_window_days": _ROLLBACK_WINDOW_DAYS,
        "preflight": asdict(preflight),
        "message": (
            "Gate 5 is ready, but live cutover execution remains disabled in "
            "this code path. Run under PO/PM approval using the production "
            "runbook."
        ),
    }
    if _EXECUTE_HOOK is None:
        return result

    hook_result = _EXECUTE_HOOK(token, preflight)
    result.update(hook_result)
    return result
