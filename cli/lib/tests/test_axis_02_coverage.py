from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from detectors.axis_02_coverage import Axis02CoverageErosion


def _create_db(db_path: Path, *, previous_counts: list[int]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE detector_runs (
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
        for count in previous_counts:
            conn.execute(
                """
                INSERT INTO detector_runs (
                    recorded_at, axis_id, detector_name, phase_gate, verdict,
                    findings_json, cost_ms, raw_json, config_json, command, db_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "2026-05-12T00:00:00Z",
                    "axis-02",
                    "coverage erosion",
                    "G4",
                    "passed",
                    "[]",
                    1,
                    json.dumps({"current_uncovered": count}),
                    "{}",
                    "run",
                    str(db_path),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_axis_02_returns_warning_on_single_worsening(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path, previous_counts=[4])
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    payload = {
        "items": [{"path": "cli/lib/sample.py"}] * 6,
        "summary": {"covered": 2, "eligible": 8, "coverage_pct": 25.0},
    }

    def fake_run(command, check, capture_output, text, cwd, env):  # type: ignore[no-untyped-def]
        return type(
            "Completed",
            (),
            {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""},
        )()

    monkeypatch.setattr("detectors.axis_02_coverage.subprocess.run", fake_run)

    result = Axis02CoverageErosion().run(db_path)

    assert result.verdict == "passed"
    assert result.findings == [
        {"path": "cli/lib/*", "prev_uncovered": 4, "curr_uncovered": 6, "delta": 2}
    ]
    assert result.raw["current_uncovered"] == 6
    assert result.raw["previous_uncovered"] == 4
    assert result.cost_ms >= 0


def test_axis_02_fails_after_three_consecutive_worsenings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path, previous_counts=[2, 4, 5])
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    payload = {
        "items": [{"path": "cli/lib/sample.py"}] * 7,
        "summary": {"covered": 1, "eligible": 8, "coverage_pct": 12.5},
    }

    def fake_run(command, check, capture_output, text, cwd, env):  # type: ignore[no-untyped-def]
        return type(
            "Completed",
            (),
            {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""},
        )()

    monkeypatch.setattr("detectors.axis_02_coverage.subprocess.run", fake_run)

    result = Axis02CoverageErosion().run(db_path)

    assert result.verdict == "failed"
    assert result.findings[0]["prev_uncovered"] == 5
    assert result.findings[0]["curr_uncovered"] == 7
    assert result.findings[0]["delta"] == 2
    assert result.raw["worsening_streak"] == 3
