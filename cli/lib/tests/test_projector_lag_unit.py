"""Projector lag helper tests for PLAN-084 Phase 4.B.5."""

from __future__ import annotations

import sqlite3

import pytest

from cli.lib.projector_lag import (
    LAG_CRITICAL_THRESHOLD,
    LAG_WARN_THRESHOLD,
    _check_projector_lag,
)


def _seed_tables(conn: sqlite3.Connection, event_count: int) -> None:
    conn.execute(
        """
        CREATE TABLE projection_state (
            projector_id TEXT NOT NULL,
            db_name TEXT NOT NULL,
            last_processed_event_id TEXT NOT NULL,
            snapshot JSON,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (projector_id, db_name)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE event_envelope (
            event_id TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            aggregate_type TEXT NOT NULL,
            db_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload JSON NOT NULL,
            correlation_id TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (db_name, event_id)
        )
        """
    )
    conn.execute(
        """
        INSERT INTO projection_state(projector_id, db_name, last_processed_event_id, snapshot, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("phase_state", "orchestration", "evt-0000", "{}", "2026-05-18T01:00:00+00:00"),
    )
    rows = [
        (
            f"evt-{index:04d}",
            "PLAN-084",
            "phase",
            "orchestration",
            "phase.transitioned",
            "{}",
            f"corr-{index:04d}",
            "2026-05-18T01:00:00+00:00",
        )
        for index in range(1, event_count + 1)
    ]
    conn.executemany(
        """
        INSERT INTO event_envelope(
            event_id, aggregate_id, aggregate_type, db_name, event_type, payload, correlation_id, occurred_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


# @helix:index id=plan084.u-projector-lag.tests domain=cli/lib/tests summary=PLAN-084 projector lag helper unit tests
def test_u_adapter_012_warns_when_projector_lag_exceeds_threshold(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DoD 検証: PLAN-084-unit-test-design.md U-ADAPTER-012 (projector lag が閾値超過したら WARN を出す)"""
    conn = sqlite3.connect(":memory:")
    try:
        _seed_tables(conn, LAG_WARN_THRESHOLD + 1)
        caplog.set_level("WARNING")

        lag = _check_projector_lag(conn, "phase_state", "orchestration")

        assert lag == LAG_WARN_THRESHOLD + 1
        assert any(record.levelname == "WARNING" and "projector lag warning" in record.getMessage() for record in caplog.records)
    finally:
        conn.close()


def test_lag_threshold_is_strict_greater_than_without_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DoD 検証: D-API-SEP-phase4b-addendum.md §D (lag == 100 では WARN しない)"""
    conn = sqlite3.connect(":memory:")
    try:
        _seed_tables(conn, LAG_WARN_THRESHOLD)
        caplog.set_level("WARNING")

        lag = _check_projector_lag(conn, "phase_state", "orchestration")

        assert lag == LAG_WARN_THRESHOLD
        assert not any(record.levelname in {"WARNING", "CRITICAL"} for record in caplog.records)
    finally:
        conn.close()


def test_lag_over_critical_threshold_emits_critical(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DoD 検証: D-API-SEP-phase4b-addendum.md §D (lag > 1000 では CRITICAL を出す)"""
    conn = sqlite3.connect(":memory:")
    try:
        _seed_tables(conn, LAG_CRITICAL_THRESHOLD + 1)
        caplog.set_level("WARNING")

        lag = _check_projector_lag(conn, "phase_state", "orchestration")

        assert lag == LAG_CRITICAL_THRESHOLD + 1
        assert any(record.levelname == "CRITICAL" and "projector lag critical" in record.getMessage() for record in caplog.records)
    finally:
        conn.close()
