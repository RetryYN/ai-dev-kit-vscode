"""PLAN-084 I-REPLAY integration tests for shadow replay gate 3."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from cli.lib.event_envelope import EventEnvelope
from cli.lib.migrations import v31_db_separation
from cli.lib.projectors import PROJECTORS
from cli.lib import uuid7_generator
from cli.lib.shadow_replay import replay_to_shadow_db


DB_NAMES = ("orchestration", "vmodel", "scrum")


def _make_event_id(seq: int) -> str:
    return f"018f4a1b-9e1c-7000-a000-{seq:012d}"


def _event(
    event_id: str,
    db_name: str,
    event_type: str,
    payload: dict[str, object],
    aggregate_id: str = "PLAN-084",
        aggregate_type: str = "phase",
        correlation_id: str | None = None,
) -> EventEnvelope:
    event_index = int(event_id[-12:], 10)
    return EventEnvelope(
        event_id=event_id,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        db_name=db_name,
        event_type=event_type,
        payload=payload,
        correlation_id=correlation_id or uuid7_generator.generate_event_id(),
        occurred_at=f"2026-05-17T00:{event_index // 60:02d}:{event_index % 60:02d}+00:00",
    )


def _recreate_schema(db_path: Path) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(v31_db_separation.EVENT_ENVELOPE_SCHEMA)
        conn.execute(v31_db_separation.PROJECTION_STATE_SCHEMA)
        for statement in v31_db_separation.EVENT_ENVELOPE_INDEXES:
            conn.execute(statement)
        conn.commit()


def _insert_events(
    db_conn_or_path: sqlite3.Connection | Path,
    envelopes: list[EventEnvelope],
    table_name: str = "event_envelope",
) -> None:
    close_after = False
    if isinstance(db_conn_or_path, sqlite3.Connection):
        conn = db_conn_or_path
    else:
        conn = sqlite3.connect(str(db_conn_or_path))
        close_after = True

    rows = [
        (
            envelope.event_id,
            envelope.aggregate_id,
            envelope.aggregate_type,
            envelope.db_name,
            envelope.event_type,
            json.dumps(envelope.payload, ensure_ascii=False, sort_keys=True),
            envelope.correlation_id,
            envelope.occurred_at,
        )
        for envelope in envelopes
    ]

    try:
        conn.executemany(
            f"""
            INSERT INTO {table_name}(
                event_id, aggregate_id, aggregate_type, db_name, event_type,
                payload, correlation_id, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        if close_after:
            conn.close()


def _seed_projection_state(
    db_path: Path, *, projector_id: str, db_name: str, snapshot: dict[str, Any], last_event_id: str
) -> None:
    with sqlite3.connect(str(db_path)) as conn:
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


def _project_events(db_name: str, events: list[EventEnvelope]) -> dict:
    projector = {
        "orchestration": PROJECTORS["phase_state"],
        "vmodel": PROJECTORS["artifact_chain"],
        "scrum": PROJECTORS["hypothesis_state"],
    }[db_name]

    snapshot = projector.initial_snapshot()
    for envelope in events:
        if envelope.db_name == db_name:
            snapshot = projector.apply(envelope, snapshot)
    return snapshot


def _snapshot_from_db(path: Path, projector_id: str, db_name: str) -> dict[str, Any]:
    with sqlite3.connect(str(path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT last_processed_event_id, snapshot
            FROM projection_state
            WHERE projector_id = ? AND db_name = ?
            """,
            (projector_id, db_name),
        ).fetchone()
        if row is None:
            return {}
        if row["snapshot"] is None:
            return {}
        return {
            "last_processed_event_id": row["last_processed_event_id"],
            "snapshot": json.loads(row["snapshot"]),
        }


@pytest.fixture
def sqlite_tmp_root(tmp_path: Path) -> Path:
    for db_name in DB_NAMES:
        _recreate_schema(tmp_path / f"{db_name}.db")
    return tmp_path


@pytest.fixture
def legacy_conn(sqlite_tmp_root: Path) -> sqlite3.Connection:
    legacy_db = sqlite3.connect(str(sqlite_tmp_root / "helix.db"))
    legacy_db.row_factory = sqlite3.Row
    legacy_db.execute(v31_db_separation.EVENT_ENVELOPE_SCHEMA)
    legacy_db.execute(v31_db_separation.PROJECTION_STATE_SCHEMA)
    for statement in v31_db_separation.EVENT_ENVELOPE_INDEXES:
        legacy_db.execute(statement)
    legacy_db.commit()
    return legacy_db


# @helix:index id=plan084.i-replay.tests domain=cli/lib/tests summary=I-REPLAY-001 to I-REPLAY-008 の結合テスト
class TestReplayIntegration:
    def test_i_replay_001_replays_1000_events_without_mismatch(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-001 (1000 event  replay 全 PASS)"""
        events = [
            _event(
                _make_event_id(index),
                "orchestration",
                "phase.transitioned",
                {"from_phase": "L1", "to_phase": "L2", "owner": "pm"},
            )
            for index in range(1, 1001)
        ]
        _insert_events(legacy_conn, events)
        expected = _project_events("orchestration", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="phase_state",
            db_name="orchestration",
            snapshot=expected,
            last_event_id=_make_event_id(1000),
        )

        result = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root),)

        assert result.failed_count == 0
        assert result.replayed_count == 1000
        assert result.skipped_count == 0
        assert result.mismatches == []
        snapshot = _snapshot_from_db(sqlite_tmp_root / "orchestration.db", "phase_state", "orchestration")
        assert snapshot["last_processed_event_id"] == _make_event_id(1000)

    def test_i_replay_002_orchestration_phase_state_accuracy(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-002 (orchestration db replay の正確性)"""
        events = [
            _event(_make_event_id(1), "orchestration", "phase.transitioned", {"from_phase": "L2", "to_phase": "L3", "owner": "pm"}),
            _event(_make_event_id(2), "orchestration", "phase.transitioned", {"from_phase": "L3", "to_phase": "L4", "owner": "pm"}),
            _event(_make_event_id(3), "orchestration", "phase.transitioned", {"from_phase": "L4", "to_phase": "L5", "owner": "pm"}),
        ]
        _insert_events(legacy_conn, events)
        expected = _project_events("orchestration", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="phase_state",
            db_name="orchestration",
            snapshot=expected,
            last_event_id=_make_event_id(3),
        )

        result = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))

        assert result.failed_count == 0
        snapshot = _snapshot_from_db(sqlite_tmp_root / "orchestration.db", "phase_state", "orchestration")
        assert snapshot["snapshot"]["current_phase"] == "L5"

    def test_i_replay_003_vmodel_artifact_replay_accuracy(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-003 (vmodel db replay の正確性)"""
        events = []
        for i in range(1, 4):
            events.append(
                _event(
                    _make_event_id(i * 2),
                    "vmodel",
                    "artifact.created",
                    {"artifact_type": "design", "plan_id": "PLAN-084", "file_path": f"docs/{i}.md", "artifact_id": f"a{i}"},
                    aggregate_type="artifact",
                    aggregate_id="PLAN-084",
                )
            )
            events.append(
                _event(
                    _make_event_id(i * 2 + 1),
                    "vmodel",
                    "artifact.linked",
                    {"artifact_id": f"a{i}", "parent_id": None},
                    aggregate_type="artifact",
                    aggregate_id="PLAN-084",
                )
            )
        _insert_events(legacy_conn, events)
        expected = _project_events("vmodel", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="artifact_chain",
            db_name="vmodel",
            snapshot=expected,
            last_event_id=_make_event_id(7),
        )

        result = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))

        assert result.failed_count == 0
        snapshot = _snapshot_from_db(sqlite_tmp_root / "vmodel.db", "artifact_chain", "vmodel")
        assert len(snapshot["snapshot"]["artifacts"]) == 3

    def test_i_replay_004_scrum_hypothesis_replay_accuracy(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-004 (scrum db replay の正確性)"""
        events = []
        for i in range(1, 4):
            events.extend(
                [
                    _event(
                        _make_event_id(i * 2),
                        "scrum",
                        "hypothesis.added",
                        {"hypothesis_id": f"h{i}"},
                        aggregate_type="hypothesis",
                        aggregate_id="PLAN-084",
                    ),
                    _event(
                        _make_event_id(i * 2 + 1),
                        "scrum",
                        "hypothesis.confirmed",
                        {"hypothesis_id": f"h{i}"},
                        aggregate_type="hypothesis",
                        aggregate_id="PLAN-084",
                    ),
                ]
            )
        _insert_events(legacy_conn, events)
        expected = _project_events("scrum", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="hypothesis_state",
            db_name="scrum",
            snapshot=expected,
            last_event_id=_make_event_id(7),
        )

        result = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))

        assert result.failed_count == 0
        snapshot = _snapshot_from_db(sqlite_tmp_root / "scrum.db", "hypothesis_state", "scrum")
        assert len([h for h in snapshot["snapshot"]["hypotheses"] if h["status"] == "confirmed"]) == 3

    def test_i_replay_005_idempotency(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-005 (同一 replay を 2 回実行して snapshot 恒久)"""
        events = [
            _event(
                _make_event_id(1),
                "orchestration",
                "phase.transitioned",
                {"from_phase": "L2", "to_phase": "L3", "owner": "pm"},
            ),
            _event(
                _make_event_id(2),
                "orchestration",
                "phase.transitioned",
                {"from_phase": "L3", "to_phase": "L4", "owner": "pm"},
            ),
        ]
        _insert_events(legacy_conn, events)
        expected = _project_events("orchestration", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="phase_state",
            db_name="orchestration",
            snapshot=expected,
            last_event_id=_make_event_id(2),
        )

        result_first = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))
        snapshot_first = _snapshot_from_db(sqlite_tmp_root / "orchestration.db", "phase_state", "orchestration")

        result_second = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))
        snapshot_second = _snapshot_from_db(sqlite_tmp_root / "orchestration.db", "phase_state", "orchestration")

        assert result_first.failed_count == 0
        assert result_second.failed_count == 0
        assert snapshot_first["snapshot"] == snapshot_second["snapshot"]
        assert snapshot_first["last_processed_event_id"] == snapshot_second["last_processed_event_id"]

    def test_i_replay_006_updates_last_processed_event_id(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-006 (last_processed_event_id が最新版へ更新される)"""
        events = [
            _event(_make_event_id(index), "orchestration", "phase.transitioned", {
                "from_phase": "L2",
                "to_phase": "L3" if index % 2 == 0 else "L4",
                "owner": "pm",
            })
            for index in range(1, 6)
        ]
        _insert_events(legacy_conn, events)
        expected = _project_events("orchestration", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="phase_state",
            db_name="orchestration",
            snapshot=expected,
            last_event_id=_make_event_id(5),
        )

        with sqlite3.connect(str(sqlite_tmp_root / "orchestration.db")) as shadow_conn:
            shadow_conn.execute(
                """
                INSERT INTO projection_state(projector_id, db_name, last_processed_event_id, snapshot, updated_at)
                VALUES ('phase_state', 'orchestration', '018f4a1b-9e1c-7000-a000-000000000000', '{}', '2026-05-17T00:00:00+00:00')
                """
            )

        replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))
        after = _snapshot_from_db(sqlite_tmp_root / "orchestration.db", "phase_state", "orchestration")

        assert after["last_processed_event_id"] == _make_event_id(5)

    def test_i_replay_007_mismatch_detected_as_fail_close(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-007 (projector mismatch を検知して fail-close)"""
        projector = PROJECTORS["phase_state"]
        original_apply = projector.apply

        def _broken_apply(envelope: EventEnvelope, current_snapshot: dict | None) -> dict:
            original_snapshot = original_apply(envelope, current_snapshot)
            broken = dict(original_snapshot)
            broken["current_phase"] = "BROKEN"
            return broken

        events = [
            _event(
                _make_event_id(1),
                "orchestration",
                "phase.transitioned",
                {"from_phase": "L2", "to_phase": "L3", "owner": "pm"},
            )
        ]
        _insert_events(legacy_conn, events)
        expected = _project_events("orchestration", events)
        _seed_projection_state(
            sqlite_tmp_root / "helix.db",
            projector_id="phase_state",
            db_name="orchestration",
            snapshot=expected,
            last_event_id=_make_event_id(1),
        )

        monkeypatch.setattr(projector, "apply", _broken_apply)
        result = replay_to_shadow_db(legacy_conn, str(sqlite_tmp_root))

        assert result.failed_count >= 1
        assert any(item["reason"] == "snapshot mismatch" for item in result.mismatches)

        monkeypatch.setattr(projector, "apply", original_apply)

    @pytest.mark.skip(reason="HELIX-SKIP: migration_pending | PLAN-084 | due_date: 2026-12-31")
    def test_i_replay_008_gate_3_all_db_pass(self, sqlite_tmp_root: Path, legacy_conn: sqlite3.Connection) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-REPLAY-008 (24h 連続 PASS gate 3 条件)"""
        assert False
