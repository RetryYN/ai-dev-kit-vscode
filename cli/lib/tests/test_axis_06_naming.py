from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from detectors.axis_06_naming import Axis06NamingConfusion


def _create_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE code_index (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                summary TEXT NOT NULL,
                path TEXT NOT NULL,
                line_no INTEGER NOT NULL,
                symbol_line INTEGER NOT NULL DEFAULT 0,
                bucket TEXT NOT NULL DEFAULT 'coverage_eligible'
            );
            """
        )
        conn.executemany(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("sample.handle_task", "cli/lib", "snake pair", "cli/lib/ops.py", 1, 1, "coverage_eligible"),
                ("sample.handle_tasks", "cli/lib", "snake pair plural", "cli/lib/ops.py", 2, 2, "coverage_eligible"),
                ("sample.load_data", "cli/lib", "snake symbol", "cli/lib/mixed.py", 1, 1, "coverage_eligible"),
                ("sample.loadData", "cli/lib", "camel symbol", "cli/lib/mixed.py", 2, 2, "coverage_eligible"),
                ("sample.architecture", "skills/legacy", "deprecated word", "skills/legacy/SKILL.md", 1, 1, "coverage_eligible"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_project_files(project_root: Path) -> None:
    (project_root / "skills" / "legacy").mkdir(parents=True, exist_ok=True)
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "skills" / "SKILL_MAP.md").write_text(
        "# SKILL_MAP\n\n## スキル群配置\n| カテゴリ | スキル |\n|---|---|\n| common/ | sample |\n",
        encoding="utf-8",
    )
    (project_root / "skills" / "legacy" / "SKILL.md").write_text(
        "# legacy\n\narchitecture is deprecated here\n",
        encoding="utf-8",
    )


def test_axis_06_detects_similar_pair_case_mix_and_deprecated_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    _write_project_files(project_root)
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis06NamingConfusion().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"similar_pair", "case_mix", "deprecated_skill"} <= kinds
    similar = next(
        finding
        for finding in result.findings
        if finding["kind"] == "similar_pair"
        and set(finding["symbols"]) == {"sample.handle_task", "sample.handle_tasks"}
    )
    assert set(similar["symbols"]) == {"sample.handle_task", "sample.handle_tasks"}
    assert similar["paths"] == ["cli/lib/ops.py"]
    case_mix = next(finding for finding in result.findings if finding["kind"] == "case_mix")
    assert case_mix["paths"] == ["cli/lib/mixed.py"]
    deprecated = next(finding for finding in result.findings if finding["kind"] == "deprecated_skill")
    assert deprecated["symbols"] == ["architecture"]
    assert deprecated["paths"] == ["skills/legacy/SKILL.md"]
    assert result.cost_ms >= 0
