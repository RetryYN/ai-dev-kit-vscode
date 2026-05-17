"""Event envelope helpers for PLAN-084 event-sourced databases.

Design references:
- docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md §2/§5/§6
- cli/lib/migrations/v31_db_separation.py
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import uuid7_generator

_ALLOWED_DB_NAMES = frozenset({"orchestration", "vmodel", "scrum"})
_ALLOWED_GATE_NAMES = frozenset(
    {"G1", "G1.5", "G1R", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11"}
)
_SQLITE_COLUMNS = (
    "event_id",
    "aggregate_id",
    "aggregate_type",
    "db_name",
    "event_type",
    "payload",
    "correlation_id",
    "occurred_at",
)


def _validate_identifier_length(name: str, value: str) -> None:
    if len(value) != 36:
        raise ValueError(f"{name} must be a 36-character UUID v7 string")


def _validate_non_empty(name: str, value: str) -> None:
    if not value:
        raise ValueError(f"{name} must not be empty")


def _validate_occurred_at(value: str) -> None:
    if not value.endswith(("+00:00", "Z")):
        raise ValueError("occurred_at must include an explicit UTC timezone (+00:00 or Z)")

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("occurred_at must be a valid ISO8601 UTC datetime") from exc

    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("occurred_at must use UTC timezone (+00:00 or Z)")


def _validate_event_type(value: str) -> None:
    _validate_non_empty("event_type", value)
    aggregate_type, separator, verb = value.partition(".")
    if separator != "." or not aggregate_type or not verb:
        raise ValueError("event_type must follow '<aggregate_type>.<verb_past>'")


def _validate_payload_schema(event_type: str, payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must be JSON serializable") from exc

    if event_type == "phase.transitioned":
        required = {"from_phase", "to_phase", "owner"}
        allowed = required | {"reason"}
        missing = sorted(required - payload.keys())
        extra = sorted(payload.keys() - allowed)
        if missing:
            raise ValueError(f"phase.transitioned payload missing required fields: {', '.join(missing)}")
        if extra:
            raise ValueError(f"phase.transitioned payload has unsupported fields: {', '.join(extra)}")
        return

    if event_type == "gate.passed":
        required = {"gate_name", "plan_id"}
        allowed = required | {"evidence"}
        missing = sorted(required - payload.keys())
        extra = sorted(payload.keys() - allowed)
        if missing:
            raise ValueError(f"gate.passed payload missing required fields: {', '.join(missing)}")
        if extra:
            raise ValueError(f"gate.passed payload has unsupported fields: {', '.join(extra)}")
        gate_name = payload["gate_name"]
        if gate_name not in _ALLOWED_GATE_NAMES:
            raise ValueError(f"gate.passed payload gate_name must be one of {sorted(_ALLOWED_GATE_NAMES)}")
        return

    if event_type == "artifact.created":
        required = {"artifact_type", "plan_id", "file_path"}
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"artifact.created payload missing required fields: {', '.join(missing)}")


def _coerce_row_values(row: sqlite3.Row | tuple[Any, ...]) -> tuple[Any, ...]:
    if hasattr(row, "keys"):
        keys = set(row.keys())
        if all(column in keys for column in _SQLITE_COLUMNS):
            return tuple(row[column] for column in _SQLITE_COLUMNS)

    values = tuple(row)
    if len(values) == len(_SQLITE_COLUMNS):
        return values
    if len(values) == len(_SQLITE_COLUMNS) + 1:
        return values[: len(_SQLITE_COLUMNS)]
    raise ValueError(
        f"SQLite row must contain {len(_SQLITE_COLUMNS)} values"
        f" (or {len(_SQLITE_COLUMNS) + 1} with created_at), got {len(values)}"
    )


# @helix:index id=event-envelope.event-envelope domain=cli/lib summary=PLAN-084 event-sourced 3 db 共通 event envelope dataclass
@dataclass(frozen=True)
class EventEnvelope:
    """Immutable event envelope aligned with the PLAN-084 v31 SQLite schema."""

    event_id: str
    aggregate_id: str
    aggregate_type: str
    db_name: str
    event_type: str
    payload: dict[str, Any]
    correlation_id: str
    occurred_at: str

    def __post_init__(self) -> None:
        _validate_identifier_length("event_id", self.event_id)
        _validate_identifier_length("correlation_id", self.correlation_id)
        _validate_non_empty("aggregate_id", self.aggregate_id)
        _validate_non_empty("aggregate_type", self.aggregate_type)
        if self.db_name not in _ALLOWED_DB_NAMES:
            allowed = ", ".join(sorted(_ALLOWED_DB_NAMES))
            raise ValueError(f"db_name must be one of {allowed}; state-store/hybrid DBs are not event-sourced")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict[str, Any]")
        _validate_event_type(self.event_type)
        _validate_payload_schema(self.event_type, self.payload)
        _validate_occurred_at(self.occurred_at)

    def to_sqlite_row(self) -> tuple[Any, ...]:
        """Return the INSERT tuple for ``event_envelope`` without DB-managed ``created_at``."""
        return (
            self.event_id,
            self.aggregate_id,
            self.aggregate_type,
            self.db_name,
            self.event_type,
            json.dumps(self.payload, ensure_ascii=False, sort_keys=True),
            self.correlation_id,
            self.occurred_at,
        )

    @classmethod
    def from_sqlite_row(cls, row: sqlite3.Row | tuple[Any, ...]) -> EventEnvelope:
        values = _coerce_row_values(row)
        return cls(
            event_id=str(values[0]),
            aggregate_id=str(values[1]),
            aggregate_type=str(values[2]),
            db_name=str(values[3]),
            event_type=str(values[4]),
            payload=json.loads(values[5]),
            correlation_id=str(values[6]),
            occurred_at=str(values[7]),
        )


# @helix:index id=event-envelope.create-event-envelope domain=cli/lib summary=validation 付き EventEnvelope factory
def create_event_envelope(
    *,
    aggregate_id: str,
    aggregate_type: str,
    db_name: str,
    event_type: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> EventEnvelope:
    """Create an ``EventEnvelope`` with generated ``event_id`` and UTC ``occurred_at``."""
    return EventEnvelope(
        event_id=uuid7_generator.generate_event_id(),
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        db_name=db_name,
        event_type=event_type,
        payload=payload,
        correlation_id=correlation_id or uuid7_generator.generate_event_id(),
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )


# @helix:index id=event-envelope.to-sqlite-row domain=cli/lib summary=EventEnvelope を SQLite INSERT tuple に変換
def to_sqlite_row(envelope: EventEnvelope) -> tuple[Any, ...]:
    """Module-level wrapper around ``EventEnvelope.to_sqlite_row``."""
    return envelope.to_sqlite_row()


# @helix:index id=event-envelope.from-sqlite-row domain=cli/lib summary=SQLite row を EventEnvelope に復元
def from_sqlite_row(row: sqlite3.Row | tuple[Any, ...]) -> EventEnvelope:
    """Module-level wrapper around ``EventEnvelope.from_sqlite_row``."""
    return EventEnvelope.from_sqlite_row(row)


__all__ = [
    "EventEnvelope",
    "create_event_envelope",
    "from_sqlite_row",
    "to_sqlite_row",
]
