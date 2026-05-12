from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from detectors.axis_05_plan_debt import Axis05PlanDebtLoop


def _write_findings_yaml(project_root: Path) -> None:
    path = project_root / ".helix" / "audit" / "deferred-findings.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "version: 1\n"
        "redaction: { applied: true, policy: test }\n"
        "findings:\n"
        "  - plan_id: PLAN-063\n"
        "    phase: G6\n"
        "    severity: medium\n"
        "    source: docs/plans/PLAN-063-helix-db-detector-system.md#/W-7\n"
        "    title: recurring carry\n"
        "    status: carried\n"
        "    target:\n"
        "      plan_id: PLAN-063\n"
        "      phase: G6\n"
        "    carry_chain:\n"
        "      - plan_id: PLAN-063\n"
        "        phase: G4\n"
        "  - plan_id: PLAN-064\n"
        "    phase: G6\n"
        "    severity: medium\n"
        "    source: docs/plans/PLAN-064.md#/carry\n"
        "    title: growing carry\n"
        "    status: carried\n"
        "    target:\n"
        "      plan_id: PLAN-064\n"
        "      phase: G6\n",
        encoding="utf-8",
    )


def _seed_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE routing_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT,
                source TEXT,
                decision TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            );
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
            );
            """
        )
        conn.executemany(
            """
            INSERT INTO routing_decisions (plan_id, source, decision, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "PLAN-063",
                    "docs/plans/PLAN-063-helix-db-detector-system.md#/W-7",
                    "retro carry",
                    "deferred debt kept for next gate",
                    "2026-05-12T00:00:00Z",
                ),
                (
                    "PLAN-063",
                    "docs/plans/PLAN-063-helix-db-detector-system.md#/W-7",
                    "retro carry",
                    "deferred debt kept again",
                    "2026-05-12T01:00:00Z",
                ),
            ],
        )
        conn.execute(
            """
            INSERT INTO detector_runs (
                recorded_at, axis_id, detector_name, phase_gate, verdict,
                findings_json, cost_ms, raw_json, config_json, command, db_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-05-12T02:00:00Z",
                "axis-05",
                "plan debt loop",
                "G6",
                "passed",
                "[]",
                3,
                json.dumps({"current_unresolved_carry_count": 1}, ensure_ascii=False),
                "{}",
                "run",
                str(db_path),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_axis_05_detects_recurring_debt_and_carry_increase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_findings_yaml(project_root)
    db_path = project_root / ".helix" / "helix.db"
    _seed_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis05PlanDebtLoop().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"recurring_debt", "carry_increase"} <= kinds
    recurring = [finding for finding in result.findings if finding["kind"] == "recurring_debt"]
    assert recurring[0]["plan_id"] == "PLAN-063"
    assert recurring[0]["occurrence_count"] == 2
    increase = [finding for finding in result.findings if finding["kind"] == "carry_increase"]
    assert increase[0]["occurrence_count"] == 2
    assert increase[0]["previous_occurrence_count"] == 1
    assert result.raw["current_unresolved_carry_count"] == 2


def test_axis_05_blocks_without_deferred_data_or_routing_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = project_root / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite3.connect(str(db_path)).close()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis05PlanDebtLoop().run(db_path)

    assert result.verdict == "blocked"
    assert result.findings == []
    assert result.raw["reason"] == "no deferred carry data or routing history"
