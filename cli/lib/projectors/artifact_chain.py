"""Artifact chain projector."""

from __future__ import annotations

from cli.lib.event_envelope import EventEnvelope


def _artifact_entry_id(envelope: EventEnvelope) -> str:
    payload = envelope.payload
    return str(payload.get("artifact_id") or payload.get("child_id") or payload.get("id") or envelope.aggregate_id)


class ArtifactChainProjector:
    """Replay artifact events into a flat artifact chain snapshot."""

    projector_id = "artifact_chain"
    target_db = "vmodel"
    interesting_event_types = (
        "artifact.created",
        "artifact.linked",
    )

    def initial_snapshot(self) -> dict:
        return {"artifacts": []}

    # @helix:index id=projectors.artifact-chain.apply domain=cli/lib/projectors summary=artifact created/linked event から artifact chain snapshot を再構成する
    def apply(self, envelope: EventEnvelope, current_snapshot: dict | None) -> dict:
        snapshot = dict(self.initial_snapshot() if current_snapshot is None else current_snapshot)
        artifacts = [dict(item) for item in snapshot.get("artifacts", [])]
        if envelope.event_type not in self.interesting_event_types:
            snapshot["artifacts"] = artifacts
            return snapshot

        payload = envelope.payload
        artifact_id = _artifact_entry_id(envelope)
        parent_id = payload.get("parent_id")
        artifact_type = payload.get("artifact_type") or payload.get("type") or envelope.aggregate_type

        by_id = {item["id"]: item for item in artifacts}
        current = by_id.get(artifact_id, {"id": artifact_id, "type": artifact_type, "parent_id": None})
        current["type"] = artifact_type
        if envelope.event_type == "artifact.linked":
            current["parent_id"] = parent_id
        else:
            current["parent_id"] = parent_id if parent_id is not None else current.get("parent_id")
        by_id[artifact_id] = current

        snapshot["artifacts"] = [by_id[key] for key in sorted(by_id)]
        return snapshot
