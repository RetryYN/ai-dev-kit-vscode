from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from detectors.axis_01_dead import Axis01DeadCodeDrift


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
                since TEXT,
                related TEXT,
                source_hash TEXT,
                bucket TEXT NOT NULL DEFAULT 'coverage_eligible',
                updated_at DATETIME
            );
            """
        )
        conn.execute(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("sample.orphan", "cli/lib", "orphan symbol", "cli/lib/orphan.py", 10, 10, "coverage_eligible"),
        )
        conn.execute(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("sample.main", "cli/lib", "main symbol", "cli/helix-sample", 1, 1, "coverage_eligible"),
        )
        conn.commit()
    finally:
        conn.close()


def test_axis_01_marks_unreferenced_non_entrypoint_symbols(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    (project_root / "skills").mkdir(parents=True, exist_ok=True)
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "cli" / "lib" / "orphan.py").write_text(
        "\n\n\n\n\n\n\n\n\n"
        "def orphan_symbol():\n    return 1\n",
        encoding="utf-8",
    )
    (project_root / "cli" / "helix-sample").write_text(
        "def main():\n    return 0\n",
        encoding="utf-8",
    )
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis01DeadCodeDrift().run(db_path)

    assert result.verdict == "failed"
    assert len(result.findings) == 1
    assert result.findings[0]["symbol_id"] == "sample.orphan"
    assert result.findings[0]["path"] == "cli/lib/orphan.py"
    assert result.findings[0]["line"] == 10
    assert result.cost_ms >= 0
