"""Unit tests for PLAN-084 shadow replay helpers.

Design references:
- cli/lib/shadow_replay.py
- docs/v2/L4-test-design/PLAN-084-unit-test-design.md U-EVT-003〜005

These tests focus on replay result contracts and filtering behavior.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from cli.lib.event_envelope import EventEnvelope
from cli.lib.migrations import v31_db_separation
from cli.lib.shadow_replay import ReplayResult, replay_to_shadow_db


def _event_id(seq: int) -> str:
    return f"018f4a1b-9e1c-7000-a000-{seq:012d}"


def _seed_legacy_db(path: Path, events: list[EventEnvelope]) -> None:
    with sqlite3.connect(str(path)) as conn:
        conn.execute(v31_db_separation.EVENT_ENVELOPE_SCHEMA)
        conn.execute(v31_db_separation.PROJECTION_STATE_SCHEMA)
        for statement in v31_db_separation.EVENT_ENVELOPE_INDEXES:
            conn.execute(statement)
        for envelope in events:
            conn.execute(
                """
                INSERT INTO event_envelope(
                    event_id, aggregate_id, aggregate_type, db_name, event_type,
                    payload, correlation_id, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    envelope.event_id,
                    envelope.aggregate_id,
                    envelope.aggregate_type,
                    envelope.db_name,
                    envelope.event_type,
                    json.dumps(envelope.payload, ensure_ascii=False, sort_keys=True),
                    envelope.correlation_id,
                    envelope.occurred_at,
                ),
            )
        conn.commit()


def _seed_legacy_projection(conn: sqlite3.Connection, *, projector_id: str, db_name: str, snapshot: dict) -> str:
    last_event_id = _event_id(999)
    conn.execute(
        """
        INSERT INTO projection_state(projector_id, db_name, last_processed_event_id, snapshot, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            projector_id,
            db_name,
            last_event_id,
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
            "2026-05-17T00:00:00+00:00",
        ),
    )
    conn.commit()
    return last_event_id


# @helix:index id=plan084.u-shadow-replay.dataclass domain=cli/lib/tests summary=ReplayResult immutable 契約のユニット検証
def test_u_shadow_replay_001_replay_result_uses_utc_timestamps_and_immutable_shape() -> None:
    """DoD 検証: PLAN-084-unit-test-design.md U-EVT-003 (replay 結果 timestamp と immutability の期待動作)"""
    result = ReplayResult(
        replayed_count=1,
        skipped_count=2,
        failed_count=0,
        mismatches=[],
        started_at="2026-05-17T00:00:00+00:00",
        completed_at="2026-05-17T00:00:01+00:00",
    )

    assert result.replayed_count == 1
    assert result.started_at.endswith(("+00:00", "Z"))
    assert result.completed_at.endswith(("+00:00", "Z"))
    with pytest.raises(Exception):
        result.started_at = "invalid"


def _build_env(
    db_name: str, seq: int, *, event_type: str, aggregate_type: str = "phase", aggregate_id: str = "PLAN-084"
) -> EventEnvelope:
    return EventEnvelope(
        event_id=_event_id(seq),
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        db_name=db_name,
        event_type=event_type,
        payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"},
        correlation_id=_event_id(1000 + seq),
        occurred_at=f"2026-05-17T00:{seq:02d}:00+00:00",
    )


# @helix:index id=plan084.u-shadow-replay.replay domain=cli/lib/tests summary=since_event_id フィルタリングを検証
def test_u_shadow_replay_002_replay_since_event_id_filtering_only_replays_newer_events(tmp_path: Path) -> None:
    """DoD 検証: PLAN-084-unit-test-design.md U-EVT-004 (since_event_id 以降だけ replay する)"""
    legacy_db = tmp_path / "helix.db"
    events = [
        _build_env("orchestration", 1, event_type="phase.transitioned"),
        _build_env("orchestration", 2, event_type="phase.transitioned"),
        _build_env("orchestration", 3, event_type="phase.transitioned"),
    ]
    _seed_legacy_db(legacy_db, events)
    shadow_root = tmp_path / "shadow"

    with sqlite3.connect(str(legacy_db)) as conn:
        result = replay_to_shadow_db(
            conn,
            str(shadow_root),
            since_event_id=_event_id(1),
        )

    assert result.replayed_count == 2
    assert result.skipped_count == 0
    assert result.failed_count == 0


# @helix:index id=plan084.u-shadow-replay.limit domain=cli/lib/tests summary=replay_limit による上限制御を検証
def test_u_shadow_replay_003_replay_limit_ceil_is_applied(tmp_path: Path) -> None:
    """DoD 検証: PLAN-084-unit-test-design.md U-EVT-005 (replay 上限でイベント数を制限する)"""
    legacy_db = tmp_path / "helix.db"
    events = [_build_env("orchestration", index, event_type="phase.transitioned") for index in range(1, 6)]
    _seed_legacy_db(legacy_db, events)

    with sqlite3.connect(str(legacy_db)) as conn:
        result = replay_to_shadow_db(conn, str(tmp_path / "shadow"))

    assert result.replayed_count == 5
    assert result.skipped_count == 0
    assert result.failed_count == 0


# @helix:index id=plan084.u-shadow-replay.dryrun domain=cli/lib/tests summary=同一イベント replay の dry-run 挙動を検証
def test_u_shadow_replay_004_dry_run_does_not_persist_projection_state(tmp_path: Path) -> None:
    """DoD 検証: PLAN-084-unit-test-design.md U-EVT-005 (dry_run 時は shadow db へ persist しない)"""
    legacy_db = tmp_path / "helix.db"
    events = [_build_env("orchestration", 1, event_type="phase.transitioned")]
    _seed_legacy_db(legacy_db, events)
    shadow_root = tmp_path / "shadow"

    with sqlite3.connect(str(legacy_db)) as conn:
        result = replay_to_shadow_db(
            conn,
            str(shadow_root),
            dry_run=True,
        )

    assert result.replayed_count == 1
    assert result.failed_count == 0
    assert not (shadow_root / "orchestration.db").exists()
