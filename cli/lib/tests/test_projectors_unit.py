"""Projector unit tests for PLAN-084 Phase 4.B.5."""

from __future__ import annotations

from cli.lib.event_envelope import EventEnvelope
from cli.lib.projectors import KNOWN_PROJECTOR_IDS, PROJECTORS, get_projector

VALID_EVENT_ID = "018f4a1b-9e1c-7000-a000-0123456789ab"
VALID_CORRELATION_ID = "018f4a1c-9e1c-7000-a000-0123456789ab"


# @helix:index id=plan084.u-proj.tests domain=cli/lib/tests summary=PLAN-084 projector 3 件 unit tests
def _make_envelope(
    *,
    aggregate_id: str,
    aggregate_type: str,
    db_name: str,
    event_type: str,
    payload: dict[str, object],
    occurred_at: str = "2026-05-18T01:00:00.000000+00:00",
) -> EventEnvelope:
    return EventEnvelope(
        event_id=VALID_EVENT_ID,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        db_name=db_name,
        event_type=event_type,
        payload=payload,
        correlation_id=VALID_CORRELATION_ID,
        occurred_at=occurred_at,
    )


def test_registry_contains_frozen_phase_4b5_projectors() -> None:
    """DoD 検証: D-API-SEP-phase4b-addendum.md §B (registry は 3 projector のみ公開する)"""
    assert KNOWN_PROJECTOR_IDS == frozenset({"phase_state", "artifact_chain", "hypothesis_state"})
    assert set(PROJECTORS) == set(KNOWN_PROJECTOR_IDS)
    assert get_projector("phase_state").target_db == "orchestration"


def test_phase_state_projector_applies_transition_from_empty_snapshot() -> None:
    """DoD 検証: D-API-SEP-phase4b-addendum.md §B (phase_state apply は current/previous/transitioned_at を返す)"""
    projector = get_projector("phase_state")
    envelope = _make_envelope(
        aggregate_id="PLAN-084",
        aggregate_type="phase",
        db_name="orchestration",
        event_type="phase.transitioned",
        payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"},
    )

    snapshot = projector.apply(envelope, None)

    assert snapshot == {
        "current_phase": "L4",
        "previous_phase": "L3",
        "transitioned_at": "2026-05-18T01:00:00.000000+00:00",
    }


def test_artifact_chain_projector_links_parent_to_existing_artifact() -> None:
    """DoD 検証: D-API-SEP-phase4b-addendum.md §B (artifact_chain apply は artifact list を parent_id 付きで返す)"""
    projector = get_projector("artifact_chain")
    created = _make_envelope(
        aggregate_id="ART-002",
        aggregate_type="artifact",
        db_name="vmodel",
        event_type="artifact.created",
        payload={
            "artifact_id": "ART-002",
            "artifact_type": "spec",
            "plan_id": "PLAN-084",
            "file_path": "docs/v2/spec.md",
        },
    )
    linked = _make_envelope(
        aggregate_id="ART-002",
        aggregate_type="artifact",
        db_name="vmodel",
        event_type="artifact.linked",
        payload={"artifact_id": "ART-002", "artifact_type": "spec", "parent_id": "ART-001"},
    )

    snapshot = projector.apply(created, None)
    snapshot = projector.apply(linked, snapshot)

    assert snapshot == {
        "artifacts": [
            {"id": "ART-002", "type": "spec", "parent_id": "ART-001"},
        ]
    }


def test_hypothesis_state_projector_updates_status_and_decided_at() -> None:
    """DoD 検証: D-API-SEP-phase4b-addendum.md §B (hypothesis_state apply は hypothesis 最終 status を返す)"""
    projector = get_projector("hypothesis_state")
    added = _make_envelope(
        aggregate_id="H-001",
        aggregate_type="hypothesis",
        db_name="scrum",
        event_type="hypothesis.added",
        payload={"hypothesis_id": "H-001"},
    )
    confirmed = _make_envelope(
        aggregate_id="H-001",
        aggregate_type="hypothesis",
        db_name="scrum",
        event_type="hypothesis.confirmed",
        payload={"hypothesis_id": "H-001"},
        occurred_at="2026-05-18T01:05:00.000000+00:00",
    )

    snapshot = projector.apply(added, None)
    snapshot = projector.apply(confirmed, snapshot)

    assert snapshot == {
        "hypotheses": [
            {
                "id": "H-001",
                "status": "confirmed",
                "decided_at": "2026-05-18T01:05:00.000000+00:00",
            }
        ]
    }
