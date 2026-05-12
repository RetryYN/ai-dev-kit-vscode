from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from detectors import registry
from detectors.base import DetectorResult


def _seed_dashboard_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
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
            );
            CREATE TABLE invocation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                role TEXT,
                model TEXT,
                task_id TEXT,
                plan_id TEXT,
                sprint TEXT,
                input_bytes INTEGER,
                output_bytes INTEGER,
                duration_ms INTEGER,
                decision TEXT,
                cost_cents REAL,
                parent_invocation_id INTEGER,
                raw_meta TEXT
            );
            CREATE TABLE code_index (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                summary TEXT NOT NULL,
                path TEXT NOT NULL,
                line_no INTEGER NOT NULL,
                symbol_line INTEGER NOT NULL DEFAULT 0,
                bucket TEXT NOT NULL DEFAULT 'coverage_eligible'
            );
            CREATE TABLE observe_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accuracy_score REAL NOT NULL,
                verdict TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE skill_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE routing_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT,
                source TEXT,
                decision TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            );
            """
        )

        now = datetime.now(timezone.utc)
        detector_rows: list[tuple[str, str, str, str | None, str, str, int, str, str, str, str]] = []
        axes = [f"axis-{idx:02d}" for idx in range(1, 15)] + ["axis-01"]
        for index, axis_id in enumerate(axes):
            verdict = "passed"
            if axis_id == "axis-01":
                verdict = "failed" if index == 0 else "passed"
            elif axis_id == "axis-02":
                verdict = "blocked"
            detector_rows.append(
                (
                    (now - timedelta(minutes=15 - index)).isoformat(),
                    axis_id,
                    f"{axis_id} detector",
                    "G4" if axis_id in {"axis-01", "axis-02", "axis-03", "axis-09", "axis-14"} else "G2",
                    verdict,
                    "[]",
                    7 + index,
                    json.dumps({"verdict": verdict}, ensure_ascii=False),
                    "{}",
                    "run",
                    str(db_path),
                )
            )
        conn.executemany(
            """
            INSERT INTO detector_runs (
                recorded_at, axis_id, detector_name, phase_gate, verdict,
                findings_json, cost_ms, raw_json, config_json, command, db_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            detector_rows,
        )

        invocation_rows = [
            ((now - timedelta(minutes=5)).isoformat(), "codex", "tl", "gpt-5.5"),
            ((now - timedelta(minutes=15)).isoformat(), "codex", "pg", "gpt-5.4"),
            ((now - timedelta(minutes=55)).isoformat(), "skill", "qa", "gpt-5.4"),
            ((now - timedelta(hours=2)).isoformat(), "hook", "qa", "gpt-5.4"),
        ]
        conn.executemany(
            """
            INSERT INTO invocation_log (timestamp, type, role, model)
            VALUES (?, ?, ?, ?)
            """,
            invocation_rows,
        )

        conn.executemany(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("sample.alpha", "cli/lib", "alpha", "cli/lib/alpha.py", 1, 1, "coverage_eligible"),
                ("sample.beta", "cli/lib", "beta", "cli/lib/beta.py", 2, 2, "coverage_eligible"),
                ("sample.gamma", "cli/lib", "gamma", "cli/lib/gamma.py", 3, 3, "coverage_eligible"),
                ("sample.delta", "cli/lib", "delta", "cli/lib/delta.py", 4, 4, "excluded"),
            ],
        )

        conn.executemany(
            """
            INSERT INTO observe_accuracy (accuracy_score, verdict, created_at)
            VALUES (?, ?, ?)
            """,
            [
                (0.84, "warn", (now - timedelta(minutes=8)).isoformat()),
                (0.91, "pass", (now - timedelta(minutes=2)).isoformat()),
            ],
        )

        skill_rows = [
            ("skill-a", (now - timedelta(days=1)).isoformat()),
            ("skill-a", (now - timedelta(days=2)).isoformat()),
            ("skill-a", (now - timedelta(days=3)).isoformat()),
            ("skill-b", (now - timedelta(days=1)).isoformat()),
            ("skill-b", (now - timedelta(days=4)).isoformat()),
            ("skill-c", (now - timedelta(days=6)).isoformat()),
        ]
        conn.executemany(
            """
            INSERT INTO skill_usage (skill_id, created_at, completed_at)
            VALUES (?, ?, NULL)
            """,
            skill_rows,
        )

        conn.executemany(
            """
            INSERT INTO routing_decisions (plan_id, source, decision, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("PLAN-063", "docs/plans/PLAN-063.md#/carry-1", "carry", "carry debt", now.isoformat()),
                ("PLAN-063", "docs/plans/PLAN-063.md#/carry-2", "carry", "carry debt", now.isoformat()),
                ("PLAN-064", "docs/plans/PLAN-064.md#/debt", "debt", "open debt", now.isoformat()),
                ("PLAN-065", "docs/plans/PLAN-065.md#/other", "review", "other routing", now.isoformat()),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _fake_run_all(_: Path, *, config: dict[str, object] | None = None) -> dict[str, DetectorResult]:
    results: dict[str, DetectorResult] = {}
    for axis_id in sorted(registry.REGISTRY.keys()):
        verdict = "passed"
        if axis_id == "axis-01":
            verdict = "failed"
        elif axis_id == "axis-02":
            verdict = "blocked"
        results[axis_id] = DetectorResult(verdict=verdict, findings=[], cost_ms=1, raw={})
    return results


def test_dashboard_aggregation_uses_all_requested_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    _seed_dashboard_db(db_path)
    monkeypatch.setattr(registry, "run_all", _fake_run_all)

    data = registry.dashboard_data(db_path)

    assert data["counts"] == {"passed": 13, "failed": 1, "blocked": 1}
    assert len(data["detector_runs"]) == 14
    assert data["invocation_log"]["total"] == 3
    assert {item["label"] for item in data["invocation_log"]["by_role"]} == {"tl", "pg", "qa"}
    assert data["code_entries"]["source_table"] == "code_index"
    assert data["code_entries"]["coverage_eligible"] == 3
    assert data["code_entries"]["uncovered_pct"] == 25.0
    assert data["observe_tables"]["tables"][0]["table"] == "observe_accuracy"
    assert data["observe_tables"]["tables"][0]["accuracy_score"] == 0.91
    assert data["skill_usage"]["top"][0]["skill_id"] == "skill-a"
    assert data["skill_usage"]["top"][0]["count"] == 3
    assert data["routing_decisions"]["carry"] == 2
    assert data["routing_decisions"]["debt"] == 1

    text = registry._render_dashboard_text(data)
    assert "detector_runs (latest 14)" in text
    assert "invocation_log (last 1h) total=3" in text
    assert "code_entries source=code_index coverage_eligible=3 uncovered%=25" in text
    assert "observe_*" in text
    assert "skill_usage (last 7d top 5)" in text
    assert "routing_decisions carry=2 debt=1 total=4" in text

    mermaid = data["mermaid"]
    assert "graph TD" in mermaid
    assert "summary[[passed=13 blocked=1 failed=1]]" in mermaid
    assert "code_entries[[code_entries<br/>coverage_eligible=3<br/>uncovered%=25]]" in mermaid
    assert "detector_runs[[detector_runs<br/>latest=14]]" in mermaid
    assert "observe_tables[[observe_*<br/>tables=1]]" in mermaid
