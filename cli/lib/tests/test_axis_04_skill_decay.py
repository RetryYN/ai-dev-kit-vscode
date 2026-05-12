from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
from pathlib import Path

import pytest

from detectors.axis_04_skill_decay import Axis04SkillDecay


def _create_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
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
                completed_at TIMESTAMP
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _insert_usage_rows(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        old = (now - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
        conn.executemany(
            """
            INSERT INTO skill_usage (task_text, skill_id, outcome, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("recent pass", "skill-one", "passed", recent),
                ("recent fail 1", "skill-one", "failed", recent),
                ("recent fail 2", "skill-one", "failed", recent),
                ("old fail", "skill-four", "failed", old),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_skill_map(project_root: Path) -> None:
    (project_root / "skills").mkdir(parents=True, exist_ok=True)
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    (project_root / "skills" / "SKILL_MAP.md").write_text(
        "# SKILL_MAP\n\n"
        "## スキル群配置\n"
        "| カテゴリ | スキル |\n"
        "|---|---|\n"
        "| common/ | **skill-one**, skill-two, skill-three, skill-four |\n",
        encoding="utf-8",
    )


def test_axis_04_marks_unused_and_failing_skills(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    _write_skill_map(project_root)
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    _insert_usage_rows(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis04SkillDecay().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"unused", "failing"} <= kinds
    unused = next(finding for finding in result.findings if finding["skill_id"] == "skill-two")
    assert unused["usage_count"] == 0
    failing = next(finding for finding in result.findings if finding["skill_id"] == "skill-one")
    assert failing["usage_count"] == 3
    assert failing["fail_ratio"] == pytest.approx(2 / 3, rel=1e-3)
    assert result.cost_ms >= 0
