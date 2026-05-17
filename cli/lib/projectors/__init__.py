"""Projector registry for PLAN-084 Phase 4.B.5."""

from __future__ import annotations

from typing import Protocol

from .artifact_chain import ArtifactChainProjector
from .hypothesis_state import HypothesisStateProjector
from .phase_state import PhaseStateProjector


class Projector(Protocol):
    """Common contract frozen by the Phase 4.B addendum."""

    projector_id: str
    target_db: str
    interesting_event_types: tuple[str, ...]

    def apply(self, envelope: object, current_snapshot: dict | None) -> dict:
        """Apply one event and return the next JSON-serializable snapshot."""

    def initial_snapshot(self) -> dict:
        """Return the empty state used before the first event is replayed."""


# @helix:index id=projectors.registry domain=cli/lib/projectors summary=PLAN-084 projector 3 件 registry
PROJECTORS: dict[str, Projector] = {
    "phase_state": PhaseStateProjector(),
    "artifact_chain": ArtifactChainProjector(),
    "hypothesis_state": HypothesisStateProjector(),
}

KNOWN_PROJECTOR_IDS = frozenset(PROJECTORS)


def get_projector(projector_id: str) -> Projector:
    """Return a registered projector or raise ``KeyError``."""
    return PROJECTORS[projector_id]


__all__ = [
    "KNOWN_PROJECTOR_IDS",
    "PROJECTORS",
    "Projector",
    "get_projector",
]
