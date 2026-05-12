from __future__ import annotations

import sqlite3
from pathlib import Path

import helix_db

from detectors.axis_11_regression import Axis11RegressionDetection


def _insert_test_row(
    conn: sqlite3.Connection,
    *,
    row_id: int,
    commit_sha: str,
    timestamp: str,
    suite: str,
    test_name: str,
    status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO test_baseline (
            id, commit_sha, timestamp, suite, test_name, status,
            duration_ms, skip_reason, code_entry_id, test_design_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (row_id, commit_sha, timestamp, suite, test_name, status, 10, None, None, None),
    )


def _db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def test_axis_11_marks_non_flaky_pass_to_fail_as_critical(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        _insert_test_row(
            conn,
            row_id=1,
            commit_sha="commit-a",
            timestamp="2026-05-12T00:00:00Z",
            suite="pytest",
            test_name="tests/test_sample.py::test_case",
            status="PASS",
        )
        _insert_test_row(
            conn,
            row_id=2,
            commit_sha="commit-b",
            timestamp="2026-05-12T01:00:00Z",
            suite="pytest",
            test_name="tests/test_sample.py::test_case",
            status="FAIL",
        )
        conn.commit()
    finally:
        conn.close()

    result = Axis11RegressionDetection().run(db_path)

    assert result.verdict == "failed"
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding["kind"] == "test_pass_to_fail"
    assert finding["severity"] == "critical"
    assert "commit-a:PASS -> commit-b:FAIL" in finding["detail"]


def test_axis_11_relaxes_flaky_pass_to_fail_to_warning(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        _insert_test_row(
            conn,
            row_id=1,
            commit_sha="commit-a",
            timestamp="2026-05-12T00:00:00Z",
            suite="pytest",
            test_name="tests/test_sample.py::test_case",
            status="FAIL",
        )
        _insert_test_row(
            conn,
            row_id=2,
            commit_sha="commit-b",
            timestamp="2026-05-12T01:00:00Z",
            suite="pytest",
            test_name="tests/test_sample.py::test_case",
            status="PASS",
        )
        _insert_test_row(
            conn,
            row_id=3,
            commit_sha="commit-c",
            timestamp="2026-05-12T02:00:00Z",
            suite="pytest",
            test_name="tests/test_sample.py::test_case",
            status="FAIL",
        )
        conn.commit()
    finally:
        conn.close()

    result = Axis11RegressionDetection().run(db_path)

    assert result.verdict == "passed"
    assert len(result.findings) == 1
    assert result.findings[0]["kind"] == "test_pass_to_fail"
    assert result.findings[0]["severity"] == "warning"


def test_axis_11_detects_contract_diff_and_silent_error_increase(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS detector_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                axis_id TEXT NOT NULL,
                detector_name TEXT NOT NULL,
                phase_gate TEXT,
                verdict TEXT NOT NULL,
                findings_json TEXT NOT NULL,
                cost_ms INTEGER NOT NULL,
                raw_json TEXT NOT NULL,
                config_json TEXT NOT NULL,
                command TEXT NOT NULL,
                db_path TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO contract_entries (
                contract_type, source_path, symbol_id, version, schema_hash,
                breaking_change_flag, introduced_plan, raw_spec, design_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "cli-contract",
                    "docs/features/demo/D-API/api.yaml",
                    "docs.features.demo.D-API.api",
                    "1.0.0",
                    "hash-old",
                    0,
                    "PLAN-063",
                    "{}",
                    "detailed",
                ),
                (
                    "cli-contract",
                    "docs/features/demo/D-API/api.yaml",
                    "docs.features.demo.D-API.api",
                    "1.1.0",
                    "hash-new",
                    1,
                    "PLAN-063",
                    "{}",
                    "detailed",
                ),
            ],
        )
        conn.executemany(
            """
            INSERT INTO detector_runs (
                recorded_at, axis_id, detector_name, phase_gate, verdict,
                findings_json, cost_ms, raw_json, config_json, command, db_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "2026-05-12T00:00:00Z",
                    "axis-08",
                    "plan-retro integrity",
                    "G6",
                    "blocked",
                    "[]",
                    1,
                    "{}",
                    "{}",
                    "run",
                    str(db_path),
                ),
                (
                    "2026-05-12T01:00:00Z",
                    "axis-08",
                    "plan-retro integrity",
                    "G6",
                    "blocked",
                    "[]",
                    1,
                    "{}",
                    "{}",
                    "run",
                    str(db_path),
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    result = Axis11RegressionDetection().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"contract_diff", "silent_error_increase"} <= kinds
    contract = [finding for finding in result.findings if finding["kind"] == "contract_diff"][0]
    assert contract["severity"] == "critical"
    silent = [finding for finding in result.findings if finding["kind"] == "silent_error_increase"][0]
    assert silent["severity"] == "warning"
