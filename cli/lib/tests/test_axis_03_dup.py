from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from detectors.axis_03_dup import Axis03RealDuplicate


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
                ("sample.alpha", "cli/lib", "alpha function", "cli/lib/alpha.py", 1, 1, "coverage_eligible"),
                ("sample.beta", "cli/lib", "beta function", "cli/lib/beta.py", 1, 1, "coverage_eligible"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def test_axis_03_detects_duplicate_function_bodies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    (project_root / "skills").mkdir(parents=True, exist_ok=True)
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "cli" / "lib" / "alpha.py").write_text(
        "def alpha(value):\n"
        "    total = value + 1\n"
        "    return total * 2\n",
        encoding="utf-8",
    )
    (project_root / "cli" / "lib" / "beta.py").write_text(
        "def beta(amount):\n"
        "    total = amount + 1\n"
        "    return total * 2\n",
        encoding="utf-8",
    )
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis03RealDuplicate().run(db_path)

    assert result.verdict == "failed"
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding["kind"] == "real_duplicate"
    assert {finding["symbol_a"], finding["symbol_b"]} == {"sample.alpha", "sample.beta"}
    assert finding["similarity"] >= 0.85
    assert result.cost_ms >= 0
