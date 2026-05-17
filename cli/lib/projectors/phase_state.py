"""Phase state projector."""

from __future__ import annotations

from cli.lib.event_envelope import EventEnvelope


class PhaseStateProjector:
    """Replay phase lifecycle events into one latest-state snapshot."""

    projector_id = "phase_state"
    target_db = "orchestration"
    interesting_event_types = (
        "phase.transitioned",
        "phase.entered",
        "phase.exited",
    )

    def initial_snapshot(self) -> dict:
        return {
            "current_phase": None,
            "previous_phase": None,
            "transitioned_at": None,
        }

    # @helix:index id=projectors.phase-state.apply domain=cli/lib/projectors summary=phase event を current/previous snapshot へ畳み込む
    def apply(self, envelope: EventEnvelope, current_snapshot: dict | None) -> dict:
        snapshot = dict(self.initial_snapshot() if current_snapshot is None else current_snapshot)
        if envelope.event_type not in self.interesting_event_types:
            return snapshot

        payload = envelope.payload
        if envelope.event_type == "phase.transitioned":
            snapshot["previous_phase"] = payload.get("from_phase")
            snapshot["current_phase"] = payload.get("to_phase")
        elif envelope.event_type == "phase.entered":
            snapshot["previous_phase"] = snapshot.get("current_phase")
            snapshot["current_phase"] = (
                payload.get("phase") or payload.get("to_phase") or payload.get("current_phase")
            )
        elif envelope.event_type == "phase.exited":
            snapshot["previous_phase"] = (
                payload.get("phase") or payload.get("from_phase") or snapshot.get("current_phase")
            )
            snapshot["current_phase"] = None

        snapshot["transitioned_at"] = envelope.occurred_at
        return snapshot
