"""Hypothesis state projector."""

from __future__ import annotations

from cli.lib.event_envelope import EventEnvelope


def _hypothesis_id(envelope: EventEnvelope) -> str:
    payload = envelope.payload
    return str(payload.get("hypothesis_id") or payload.get("id") or envelope.aggregate_id)


class HypothesisStateProjector:
    """Replay hypothesis lifecycle events into one state snapshot."""

    projector_id = "hypothesis_state"
    target_db = "scrum"
    interesting_event_types = (
        "hypothesis.added",
        "hypothesis.confirmed",
        "hypothesis.rejected",
    )

    def initial_snapshot(self) -> dict:
        return {"hypotheses": []}

    # @helix:index id=projectors.hypothesis-state.apply domain=cli/lib/projectors summary=hypothesis lifecycle event から最新 status snapshot を再構成する
    def apply(self, envelope: EventEnvelope, current_snapshot: dict | None) -> dict:
        snapshot = dict(self.initial_snapshot() if current_snapshot is None else current_snapshot)
        hypotheses = [dict(item) for item in snapshot.get("hypotheses", [])]
        if envelope.event_type not in self.interesting_event_types:
            snapshot["hypotheses"] = hypotheses
            return snapshot

        hypothesis_id = _hypothesis_id(envelope)
        by_id = {item["id"]: item for item in hypotheses}
        current = by_id.get(hypothesis_id, {"id": hypothesis_id, "status": "pending", "decided_at": None})

        if envelope.event_type == "hypothesis.added":
            current["status"] = "pending"
            current["decided_at"] = None
        elif envelope.event_type == "hypothesis.confirmed":
            current["status"] = "confirmed"
            current["decided_at"] = envelope.occurred_at
        elif envelope.event_type == "hypothesis.rejected":
            current["status"] = "rejected"
            current["decided_at"] = envelope.occurred_at

        by_id[hypothesis_id] = current
        snapshot["hypotheses"] = [by_id[key] for key in sorted(by_id)]
        return snapshot
