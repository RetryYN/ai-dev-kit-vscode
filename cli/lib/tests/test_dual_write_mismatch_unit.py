"""Unit tests for cli/lib/dual_write_mismatch.py.

設計参照:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md §C
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from cli.lib.dual_write_mismatch import check_dual_write_mismatch
from cli.lib.migrations import v32_detector_runs

TABLE_SQL = """
CREATE TABLE sample_records (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _seed_rows(conn: sqlite3.Connection, rows: list[tuple[int, str, str]]) -> None:
    conn.executemany(
        "INSERT INTO sample_records (id, name, updated_at) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()


@pytest.fixture
def dual_write_fixture(tmp_path: Path) -> tuple[sqlite3.Connection, sqlite3.Connection]:
    legacy_conn = _connect(tmp_path / "legacy.db")
    backend_conn = _connect(tmp_path / "backend.db")
    legacy_conn.execute(TABLE_SQL)
    backend_conn.execute(TABLE_SQL)
    backend_conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    backend_conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (31, '2026-05-18T00:00:00+00:00')"
    )
    backend_conn.commit()
    v32_detector_runs.migrate_v31_to_v32(backend_conn)

    try:
        yield legacy_conn, backend_conn
    finally:
        legacy_conn.close()
        backend_conn.close()


# @helix:index id=plan084.u-mismatch.tests domain=cli/lib/tests summary=PLAN-084 dual-write mismatch detector unit tests
class TestDualWriteMismatch:
    def test_u_mismatch_001_returns_clean_result_and_records_pass(
        self,
        dual_write_fixture: tuple[sqlite3.Connection, sqlite3.Connection],
    ) -> None:
        """DoD 検証: PLAN-084 Phase 4.B.6 U-MISMATCH-001 (一致時は detected=False で pass record)"""
        legacy_conn, backend_conn = dual_write_fixture
        rows = [
            (1, "alice", "2026-05-18T01:00:00+00:00"),
            (2, "bob", "2026-05-18T01:05:00+00:00"),
        ]
        _seed_rows(legacy_conn, rows)
        _seed_rows(backend_conn, rows)

        result = check_dual_write_mismatch(legacy_conn, backend_conn, "sample_records")

        recorded = backend_conn.execute(
            "SELECT verdict, findings_json, raw_json FROM detector_runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()

        assert result.detected is False
        assert result.mismatch_keys == []
        assert result.legacy_row_count == 2
        assert result.new_row_count == 2
        assert result.severity == "warn"
        assert recorded["verdict"] == "passed"
        assert json.loads(recorded["findings_json"]) == []
        assert json.loads(recorded["raw_json"])["detected"] is False

    def test_u_mismatch_002_marks_row_count_divergence_as_critical(
        self,
        dual_write_fixture: tuple[sqlite3.Connection, sqlite3.Connection],
    ) -> None:
        """DoD 検証: PLAN-084 Phase 4.B.6 U-MISMATCH-002 (行数差分は critical)"""
        legacy_conn, backend_conn = dual_write_fixture
        _seed_rows(legacy_conn, [(1, "alice", "2026-05-18T01:00:00+00:00")])
        _seed_rows(
            backend_conn,
            [
                (1, "alice", "2026-05-18T01:00:00+00:00"),
                (2, "bob", "2026-05-18T01:05:00+00:00"),
            ],
        )

        result = check_dual_write_mismatch(legacy_conn, backend_conn, "sample_records")

        assert result.detected is True
        assert result.severity == "critical"
        assert result.legacy_row_count == 1
        assert result.new_row_count == 2
        assert "2" in result.mismatch_keys

    def test_u_mismatch_003_marks_sampled_payload_difference_as_warn(
        self,
        dual_write_fixture: tuple[sqlite3.Connection, sqlite3.Connection],
    ) -> None:
        """DoD 検証: PLAN-084 Phase 4.B.6 U-MISMATCH-003 (同 key の payload 差分は warn)"""
        legacy_conn, backend_conn = dual_write_fixture
        _seed_rows(legacy_conn, [(1, "alice", "2026-05-18T01:00:00+00:00")])
        _seed_rows(backend_conn, [(1, "ALICE", "2026-05-18T01:00:00+00:00")])

        result = check_dual_write_mismatch(legacy_conn, backend_conn, "sample_records")

        recorded = backend_conn.execute(
            "SELECT verdict, raw_json FROM detector_runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()

        assert result.detected is True
        assert result.severity == "warn"
        assert result.mismatch_keys == ["1"]
        assert recorded["verdict"] == "failed"
        assert json.loads(recorded["raw_json"])["severity"] == "warn"

    def test_u_mismatch_004_caps_sample_size_to_1000(
        self,
        dual_write_fixture: tuple[sqlite3.Connection, sqlite3.Connection],
    ) -> None:
        """DoD 検証: PLAN-084 Phase 4.B.6 U-MISMATCH-004 (sample_size は 1000 で上限 clamp)"""
        legacy_conn, backend_conn = dual_write_fixture
        legacy_rows = [
            (index, f"name-{index}", "2026-05-18T01:00:00+00:00")
            for index in range(1, 1006)
        ]
        backend_rows = list(legacy_rows)
        backend_rows[-1] = (1005, "changed-after-cap", "2026-05-18T01:00:00+00:00")
        _seed_rows(legacy_conn, legacy_rows)
        _seed_rows(backend_conn, backend_rows)

        result = check_dual_write_mismatch(
            legacy_conn,
            backend_conn,
            "sample_records",
            sample_size=5000,
        )

        recorded = backend_conn.execute(
            "SELECT config_json FROM detector_runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()

        assert result.detected is False
        assert json.loads(recorded["config_json"])["sample_size"] == 1000

    def test_u_mismatch_005_rejects_non_positive_sample_size(
        self,
        dual_write_fixture: tuple[sqlite3.Connection, sqlite3.Connection],
    ) -> None:
        """DoD 検証: PLAN-084 Phase 4.B.6 U-MISMATCH-005 (sample_size <= 0 は拒否)"""
        legacy_conn, backend_conn = dual_write_fixture

        with pytest.raises(ValueError, match="sample_size must be greater than 0"):
            check_dual_write_mismatch(legacy_conn, backend_conn, "sample_records", sample_size=0)
