from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
from pathlib import Path

import pytest

from detectors.axis_13_model_skill import Axis13ModelSkillAnalytics


def _create_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE invocation_log (
                id INTEGER PRIMARY KEY,
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

            CREATE TABLE skill_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_text TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                references_used TEXT,
                agent_used TEXT,
                match_score REAL,
                match_reason TEXT,
                outcome TEXT,
                user_feedback TEXT,
                result_stdout TEXT,
                result_stderr TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                tokens_used INTEGER,
                model_used TEXT,
                fallback_applied INTEGER DEFAULT 0
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _seed_invocations(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        now = datetime.now(timezone.utc)
        rows = [
            (now - timedelta(hours=10), "se", "gpt-5.4", 100, 50, 1000, "passed", 1.0),
            (now - timedelta(hours=9), "se", "gpt-5.4", 150, 50, 2000, "failed", 3.0),
            (now - timedelta(hours=8), "se", "gpt-5.4", 120, 40, 1500, "passed", 2.0),
            (now - timedelta(hours=7), "pg", "gpt-5.3-codex-spark", 80, 20, 800, "passed", 0.5),
            (now - timedelta(hours=6), "pg", "gpt-5.3-codex-spark", 120, 30, 1200, "passed", 0.7),
            (now - timedelta(hours=5), "pg", "gpt-5.3-codex-spark", 100, 20, 1000, "blocked", 0.6),
        ]
        conn.executemany(
            """
            INSERT INTO invocation_log (
                timestamp, type, role, model, task_id, plan_id, sprint,
                input_bytes, output_bytes, duration_ms, decision, cost_cents,
                parent_invocation_id, raw_meta
            )
            VALUES (?, 'codex', ?, ?, 'W-8', 'PLAN-063', '.2', ?, ?, ?, ?, ?, NULL, '{}')
            """,
            [
                (
                    timestamp.isoformat(),
                    role,
                    model,
                    input_bytes,
                    output_bytes,
                    duration_ms,
                    decision,
                    cost_cents,
                )
                for timestamp, role, model, input_bytes, output_bytes, duration_ms, decision, cost_cents in rows
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _seed_skill_usage(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        now = datetime.now(timezone.utc)
        rows = []
        for offset, tokens in enumerate((70, 80, 90, 100, 110, 120, 130)):
            created_at = (now - timedelta(days=6 - offset)).isoformat()
            rows.append(
                (
                    f"task-{offset}",
                    "skill-a" if offset < 4 else "skill-b",
                    "failed" if offset in (1, 2, 5) else "passed",
                    "codex",
                    "gpt-5.4-mini" if offset in (0, 1, 2) else "gpt-5.3-codex",
                    1 if offset in (0, 1, 2) else 0,
                    created_at,
                    tokens,
                )
            )
        rows.append(
            (
                "task-sonnet",
                "skill-c",
                "passed",
                "sonnet",
                "claude-haiku-4-5-20251001",
                1,
                now.isoformat(),
                55,
            )
        )
        conn.executemany(
            """
            INSERT INTO skill_usage (
                task_text, skill_id, outcome, agent_used, model_used,
                fallback_applied, created_at, tokens_used
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def _write_role_configs(project_root: Path) -> None:
    roles_dir = project_root / "cli" / "roles"
    roles_dir.mkdir(parents=True, exist_ok=True)
    (roles_dir / "se.conf").write_text("codex_thinking=high\n", encoding="utf-8")
    (roles_dir / "pg.conf").write_text("codex_thinking=medium\n", encoding="utf-8")
    (roles_dir / "pmo-sonnet.conf").write_text("codex_thinking=medium\n", encoding="utf-8")


def test_axis_13_aggregates_all_analytics_views(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    _write_role_configs(project_root)
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    _seed_invocations(db_path)
    _seed_skill_usage(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis13ModelSkillAnalytics().run(db_path)

    assert result.verdict == "failed"
    summary = result.raw["summary"]

    model_map = {item["model"]: item for item in summary["models"]}
    assert set(model_map) == {"gpt-5.4", "gpt-5.3-codex-spark"}
    assert model_map["gpt-5.4"]["invocations"] == 3
    assert model_map["gpt-5.4"]["avg_tokens"] == pytest.approx((150 + 200 + 160) / 3, rel=1e-3)
    assert model_map["gpt-5.4"]["avg_cost_cents"] == pytest.approx(2.0, rel=1e-3)

    role_map = {item["role"]: item for item in summary["roles"]}
    assert role_map["se"]["invocations"] == 3
    assert role_map["se"]["error_rate"] == pytest.approx(1 / 3, rel=1e-3)
    assert role_map["pg"]["error_rate"] == pytest.approx(1 / 3, rel=1e-3)

    skill_map = {item["skill_id"]: item for item in summary["skills"]}
    assert skill_map["skill-a"]["usage_count"] == 4
    assert skill_map["skill-a"]["outcomes"]["failed"] == 2
    assert skill_map["skill-b"]["usage_count"] == 3

    thinking_map = {item["thinking"]: item for item in summary["thinking_levels"]}
    assert thinking_map["high"]["avg_duration_ms"] == pytest.approx(1500.0, rel=1e-3)
    assert thinking_map["medium"]["avg_duration_ms"] == pytest.approx(1000.0, rel=1e-3)

    fallback_map = {item["label"]: item for item in summary["fallback_rates"]}
    assert fallback_map["codex->gpt-5.4-mini"]["fallback_rate"] == pytest.approx(1.0, rel=1e-3)
    assert fallback_map["codex->gpt-5.3-codex"]["fallback_rate"] == pytest.approx(0.0, rel=1e-3)
    assert "sonnet->claude-haiku-4-5-20251001" in fallback_map

    assert len(summary["daily_tokens"]) == 7
    assert [item["tokens"] for item in summary["daily_tokens"]] == [70, 80, 90, 100, 110, 120, 185]

    kinds = {finding["kind"] for finding in result.findings}
    assert {"role_error_rate", "fallback_rate"} <= kinds
    assert result.raw["anomaly_count"] == len(result.findings)
