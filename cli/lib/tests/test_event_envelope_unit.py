"""U-EVT unit tests for cli/lib/event_envelope.py.

設計参照:
- docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md §2/§5/§6
- docs/v2/L4-test-design/PLAN-084-unit-test-design.md §3 (U-EVT-001〜010)

DoD 検証: U-EVT-001〜010
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta

import pytest

from cli.lib.event_envelope import (
    EventEnvelope,
    create_event_envelope,
    from_sqlite_row,
    to_sqlite_row,
)

VALID_EVENT_ID = "018f4a1b-9e1c-7000-a000-0123456789ab"
VALID_CORRELATION_ID = "018f4a1c-9e1c-7000-a000-0123456789ab"


# @helix:index id=plan084.u-evt.tests domain=cli/lib/tests summary=PLAN-084 EventEnvelope unit tests
def _make_envelope(**overrides: object) -> EventEnvelope:
    payload = {
        "from_phase": "L3",
        "to_phase": "L4",
        "owner": "pm-opus",
    }
    base = {
        "event_id": VALID_EVENT_ID,
        "aggregate_id": "PLAN-084",
        "aggregate_type": "phase",
        "db_name": "orchestration",
        "event_type": "phase.transitioned",
        "payload": payload,
        "correlation_id": VALID_CORRELATION_ID,
        "occurred_at": "2026-05-18T01:00:00.000000+00:00",
    }
    base.update(overrides)
    return EventEnvelope(**base)


class TestEventEnvelope:
    def test_u_evt_001_is_immutable_when_frozen(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-001 (frozen=True で immutable)"""
        envelope = _make_envelope()

        with pytest.raises(FrozenInstanceError):
            envelope.event_id = "018f4a1d-9e1c-7000-a000-0123456789ab"  # type: ignore[misc]

    def test_u_evt_002_validates_allowed_db_names(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-002 (db_name 許可値 validation)"""
        for db_name in ("orchestration", "vmodel", "scrum"):
            envelope = _make_envelope(db_name=db_name)
            assert envelope.db_name == db_name

        for db_name in ("backend", "plan", ""):
            with pytest.raises(ValueError):
                _make_envelope(db_name=db_name)

    def test_u_evt_003_factory_generates_iso8601_utc_occurred_at(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-003 (factory が UTC occurred_at を生成する)"""
        envelope = create_event_envelope(
            aggregate_id="PLAN-084",
            aggregate_type="phase",
            db_name="orchestration",
            event_type="phase.transitioned",
            payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"},
            correlation_id=VALID_CORRELATION_ID,
        )

        parsed = datetime.fromisoformat(envelope.occurred_at)
        assert envelope.occurred_at.endswith("+00:00")
        assert parsed.utcoffset() == timedelta(0)
        assert len(envelope.event_id) == 36

    def test_u_evt_004_to_sqlite_row_returns_schema_aligned_tuple(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-004 (to_sqlite_row は 8 要素 tuple を返す)"""
        payload = {"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"}
        envelope = _make_envelope(payload=payload)

        row = to_sqlite_row(envelope)

        assert len(row) == 8
        assert row == (
            VALID_EVENT_ID,
            "PLAN-084",
            "phase",
            "orchestration",
            "phase.transitioned",
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            VALID_CORRELATION_ID,
            "2026-05-18T01:00:00.000000+00:00",
        )

    def test_u_evt_005_from_sqlite_row_round_trips_losslessly(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-005 (SQLite round-trip 完全一致)"""
        envelope = _make_envelope(
            payload={
                "from_phase": "L3",
                "to_phase": "L4",
                "owner": "pm-opus",
                "reason": "handover completed",
            }
        )

        restored = from_sqlite_row(to_sqlite_row(envelope))

        assert restored == envelope

    def test_u_evt_006_validates_phase_transitioned_payload(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-006 (phase.transitioned payload schema)"""
        envelope = _make_envelope(
            event_type="phase.transitioned",
            payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"},
        )
        assert envelope.payload["to_phase"] == "L4"

        with pytest.raises(ValueError, match="missing required fields: from_phase"):
            _make_envelope(
                event_type="phase.transitioned",
                payload={"to_phase": "L4", "owner": "pm-opus"},
            )

    def test_u_evt_007_validates_gate_passed_payload(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-007 (gate.passed payload schema)"""
        envelope = _make_envelope(
            aggregate_type="gate",
            event_type="gate.passed",
            payload={"gate_name": "G4", "plan_id": "PLAN-084"},
        )
        assert envelope.payload["gate_name"] == "G4"

        with pytest.raises(ValueError, match="gate_name must be one of"):
            _make_envelope(
                aggregate_type="gate",
                event_type="gate.passed",
                payload={"gate_name": "G99", "plan_id": "PLAN-084"},
            )

    def test_u_evt_008_accepts_artifact_created_payload_and_naming(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-008 (artifact.created payload / event_type 命名)"""
        envelope = _make_envelope(
            aggregate_type="artifact",
            event_type="artifact.created",
            payload={
                "artifact_type": "design",
                "plan_id": "PLAN-084",
                "file_path": "docs/v2/D-API.md",
            },
        )

        assert envelope.event_type == "artifact.created"
        assert envelope.event_type.count(".") == 1

    def test_u_evt_009_rejects_state_store_and_hybrid_db_names(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-009 (state-store / hybrid db を拒否する)"""
        for db_name in ("backend", "frontend", "plan"):
            with pytest.raises(ValueError, match="orchestration, scrum, vmodel"):
                create_event_envelope(
                    aggregate_id="PLAN-084",
                    aggregate_type="phase",
                    db_name=db_name,
                    event_type="phase.transitioned",
                    payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"},
                    correlation_id=VALID_CORRELATION_ID,
                )

    def test_u_evt_010_rejects_local_time_without_utc_timezone(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-EVT-010 (local time は拒否される)"""
        with pytest.raises(ValueError, match="UTC timezone"):
            _make_envelope(occurred_at="2026-05-18T10:00:00")
