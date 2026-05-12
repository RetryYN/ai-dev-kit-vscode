from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from detectors.axis_12_connection import Axis12ConnectionDeficiency


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
            CREATE TABLE code_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_entry_id INTEGER NOT NULL,
                to_entry_id INTEGER,
                to_external_ref TEXT,
                edge_type TEXT NOT NULL,
                weight INTEGER DEFAULT 1,
                source_line INTEGER,
                raw_meta TEXT
            );
            """
        )
        conn.execute(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "sample.existing",
                "cli/lib",
                "existing module",
                "cli/lib/existing.py",
                1,
                1,
                "coverage_eligible",
            ),
        )
        conn.execute(
            """
            INSERT INTO code_edges (from_entry_id, to_entry_id, to_external_ref, edge_type, weight, source_line, raw_meta)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                101,
                None,
                "cli.lib.missing_module",
                "import",
                1,
                3,
                '{"source_path":"cli/lib/example.py"}',
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_axis_12_detects_broken_import_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis12ConnectionDeficiency().run(db_path)

    assert result.verdict == "failed"
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding["kind"] == "import_broken"
    assert finding["path"] == "cli.lib.missing_module"
    assert "not found in code_index/code_entries" in finding["detail"]
