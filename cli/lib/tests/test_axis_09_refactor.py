from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from detectors.axis_09_refactor import Axis09RefactorOpportunity


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
            CREATE TABLE routing_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                decision TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        rows = [
            (
                f"god.symbol.{index}",
                "cli/lib",
                f"symbol {index}",
                "cli/lib/god_file.py",
                index + 1,
                index + 1,
                "coverage_eligible",
            )
            for index in range(31)
        ]
        rows.append(("sample.args", "cli/lib", "argument explosion", "cli/lib/args.py", 1, 1, "coverage_eligible"))
        conn.executemany(
            """
            INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.executemany(
            """
            INSERT INTO routing_decisions (path, decision, detail, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("cli/lib/args.py", "refactor carry", "needs carry", "2026-05-12T00:00:00Z"),
                ("cli/lib/args.py", "refactor carry", "still needs carry", "2026-05-12T00:01:00Z"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def test_axis_09_detects_god_file_argument_explosion_and_refactor_carry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    (project_root / "skills").mkdir(parents=True, exist_ok=True)
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    god_file = "\n".join(f"def symbol_{index}():\n    return {index}" for index in range(31))
    (project_root / "cli" / "lib" / "god_file.py").write_text(god_file + "\n", encoding="utf-8")
    (project_root / "cli" / "lib" / "args.py").write_text(
        "def overloaded(a, b, c, d, e, f, g):\n"
        "    return a + b + c + d + e + f + g\n",
        encoding="utf-8",
    )
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis09RefactorOpportunity().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"god_file", "arg_explosion", "refactor_carry"} <= kinds
    god_findings = [finding for finding in result.findings if finding["kind"] == "god_file"]
    assert god_findings[0]["path"] == "cli/lib/god_file.py"
    assert "31 symbols" in god_findings[0]["detail"]
    arg_findings = [finding for finding in result.findings if finding["kind"] == "arg_explosion"]
    assert arg_findings[0]["path"] == "cli/lib/args.py"
    assert "7 args" in arg_findings[0]["detail"]
    carry_findings = [finding for finding in result.findings if finding["kind"] == "refactor_carry"]
    assert carry_findings[0]["path"] == "cli/lib/args.py"
    assert "2 consecutive" in carry_findings[0]["detail"]
    assert result.cost_ms >= 0
