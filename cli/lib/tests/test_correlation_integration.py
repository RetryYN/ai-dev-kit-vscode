"""I-CORR integration tests for PLAN-084 correlation cross-db trace.

設計参照:
- docs/v2/L4-test-design/PLAN-084-integration-test-design.md §5 (I-CORR-001〜006)

DoD 検証: I-CORR-001〜006
"""

from __future__ import annotations

import queue
import sqlite3
import threading
from pathlib import Path

import pytest

from cli.lib.correlation_context import current_correlation_id, correlation_context
from cli.lib.compatibility_adapter import read_cross_db_projection
from cli.lib.event_envelope import create_event_envelope, to_sqlite_row
from cli.lib.migrations import v31_db_separation


DB_NAMES = ("orchestration", "vmodel", "scrum")


def _create_event_schema(db_path: Path) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(v31_db_separation.EVENT_ENVELOPE_SCHEMA)
        conn.execute(v31_db_separation.PROJECTION_STATE_SCHEMA)
        for statement in v31_db_separation.EVENT_ENVELOPE_INDEXES:
            conn.execute(statement)
        conn.commit()


def _insert_event(
    db_path: Path, db_name: str, aggregate_id: str = "PLAN-084"
) -> str:
    envelope = create_event_envelope(
        aggregate_id=aggregate_id,
        aggregate_type="phase",
        db_name=db_name,
        event_type="phase.transitioned",
        payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"},
        correlation_id=current_correlation_id(),
    )
    row = to_sqlite_row(envelope)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO event_envelope(
                event_id, aggregate_id, aggregate_type, db_name, event_type,
                payload, correlation_id, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )
        conn.commit()
    return envelope.correlation_id


def _query_events_by_correlation(db_path: Path, correlation_id: str) -> list[sqlite3.Row]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM event_envelope WHERE correlation_id = ?",
            (correlation_id,),
        ).fetchall()


@pytest.fixture
def sqlite_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HELIX_DB_PATH", str(tmp_path / "helix.db"))
    for db_name in DB_NAMES:
        _create_event_schema(tmp_path / f"{db_name}.db")
    return tmp_path


# @helix:index id=plan084.i-corr.tests domain=cli/lib/tests summary=PLAN-084 correlation cross-db trace integration tests
class TestCorrelationCrossDb:
    def test_i_corr_001_orchestration_to_vmodel_inherits_correlation(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-CORR-001 (orchestration.db で correlation_id を発行 → vmodel.db に継承される)"""
        orchestration_db = sqlite_tmp_root / "orchestration.db"
        vmodel_db = sqlite_tmp_root / "vmodel.db"

        with correlation_context() as correlation_id:
            _insert_event(orchestration_db, "orchestration")
            with correlation_context(parent=correlation_id) as inner:
                _insert_event(vmodel_db, "vmodel")

            orchestration_rows = _query_events_by_correlation(orchestration_db, correlation_id)
            vmodel_rows = _query_events_by_correlation(vmodel_db, correlation_id)

        assert len(orchestration_rows) == 1
        assert len(vmodel_rows) == 1
        assert orchestration_rows[0]["correlation_id"] == correlation_id
        assert orchestration_rows[0]["correlation_id"] == inner
        assert vmodel_rows[0]["correlation_id"] == correlation_id
        assert vmodel_rows[0]["correlation_id"] == inner

    def test_i_corr_002_same_command_shared_correlation_across_three_dbs(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-CORR-002 (同一 CLI command 内の全 event が同一 correlation_id を共有する)"""
        orchestration_db = sqlite_tmp_root / "orchestration.db"
        vmodel_db = sqlite_tmp_root / "vmodel.db"
        scrum_db = sqlite_tmp_root / "scrum.db"

        with correlation_context():
            shared_correlation = current_correlation_id()
            assert shared_correlation is not None
            _insert_event(orchestration_db, "orchestration")
            _insert_event(vmodel_db, "vmodel")
            _insert_event(scrum_db, "scrum")

        assert shared_correlation is not None
        orchestration_rows = _query_events_by_correlation(orchestration_db, shared_correlation)
        vmodel_rows = _query_events_by_correlation(vmodel_db, shared_correlation)
        scrum_rows = _query_events_by_correlation(scrum_db, shared_correlation)

        assert len(orchestration_rows) == 1
        assert len(vmodel_rows) == 1
        assert len(scrum_rows) == 1
        assert {row["correlation_id"] for row in orchestration_rows + vmodel_rows + scrum_rows} == {shared_correlation}

    def test_i_corr_003_cross_db_query_returns_same_correlation(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-CORR-003 (cross-db query で 2 db を横断して correlation_id 検索ができる)"""
        orchestration_db = sqlite_tmp_root / "orchestration.db"
        vmodel_db = sqlite_tmp_root / "vmodel.db"

        with correlation_context() as correlation_id:
            _insert_event(orchestration_db, "orchestration")
            _insert_event(vmodel_db, "vmodel")

        orchestration_rows = _query_events_by_correlation(orchestration_db, correlation_id)
        vmodel_rows = _query_events_by_correlation(vmodel_db, correlation_id)
        total = orchestration_rows + vmodel_rows

        assert len(orchestration_rows) == 1
        assert len(vmodel_rows) == 1
        assert len(total) == 2
        assert len({row["correlation_id"] for row in total}) == 1

    def test_i_corr_004_threads_get_independent_correlation_ids(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-CORR-004 (別 thread では別 correlation_id が発行される)"""
        orchestration_db = sqlite_tmp_root / "orchestration.db"
        results: queue.Queue[tuple[str, str]] = queue.Queue()

        def _worker(label: str) -> None:
            with correlation_context() as correlation_id:
                _insert_event(orchestration_db, "orchestration")
                results.put((label, correlation_id))

        thread_a = threading.Thread(target=_worker, args=("A",), name="corr-thread-A")
        thread_b = threading.Thread(target=_worker, args=("B",), name="corr-thread-B")
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        label_a, correlation_a = results.get_nowait()
        label_b, correlation_b = results.get_nowait()
        assert label_a != label_b
        assert correlation_a != correlation_b
        assert _query_events_by_correlation(orchestration_db, correlation_a)
        assert _query_events_by_correlation(orchestration_db, correlation_b)

    def test_i_corr_005_nested_context_inherits_parent(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-CORR-005 (nested context は parent の correlation_id を継承する)"""
        orchestration_db = sqlite_tmp_root / "orchestration.db"

        with correlation_context() as parent_id:
            with correlation_context(parent=parent_id) as child_id:
                _insert_event(orchestration_db, "orchestration")
                assert child_id == parent_id
                assert current_correlation_id() == parent_id

            assert current_correlation_id() == parent_id

        rows = _query_events_by_correlation(orchestration_db, parent_id)
        assert len(rows) == 1
        assert rows[0]["correlation_id"] == parent_id

    def test_i_corr_006_read_cross_db_projection_and_trace_are_independent(self, sqlite_tmp_root: Path) -> None:
        """DoD 検証: PLAN-084-integration-test-design.md I-CORR-006 (read_cross_db_projection と correlation trace が独立して機能する)"""
        orchestration_db = sqlite_tmp_root / "orchestration.db"
        vmodel_db = sqlite_tmp_root / "vmodel.db"
        scrum_db = sqlite_tmp_root / "scrum.db"

        with sqlite3.connect(str(orchestration_db)) as conn:
            conn.execute(
                """
                INSERT INTO projection_state(
                    projector_id, db_name, last_processed_event_id, snapshot, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "phase_state",
                    "orchestration",
                    "018f4a1b-9e1c-7000-a000-0123456789ab",
                    '{"current_phase":"L4","previous_phase":"L3"}',
                    "2026-05-18T01:00:00+00:00",
                ),
            )
            conn.commit()

        with correlation_context() as correlation_id:
            _insert_event(orchestration_db, "orchestration")
            _insert_event(vmodel_db, "vmodel")
            _insert_event(scrum_db, "scrum")

        snapshot = read_cross_db_projection("phase_state", "orchestration")
        orchestration_rows = _query_events_by_correlation(orchestration_db, correlation_id)
        vmodel_rows = _query_events_by_correlation(vmodel_db, correlation_id)
        scrum_rows = _query_events_by_correlation(scrum_db, correlation_id)

        assert snapshot is not None
        assert snapshot["current_phase"] == "L4"
        assert len(orchestration_rows) == 1
        assert len(vmodel_rows) == 1
        assert len(scrum_rows) == 1
        for row in orchestration_rows + vmodel_rows + scrum_rows:
            assert row["correlation_id"] == correlation_id
