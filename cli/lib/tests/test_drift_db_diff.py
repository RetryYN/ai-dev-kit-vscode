import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import drift_db_diff


def _write_design_doc(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def _create_db(path: Path, statements: list[str]) -> Path:
    conn = sqlite3.connect(path)
    try:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
    finally:
        conn.close()
    return path


def test_main_reports_ok_for_matching_design_and_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    doc_path = _write_design_doc(
        tmp_path / "D-DB.md",
        """
        CREATE TABLE users (
          id INTEGER PRIMARY KEY,
          email TEXT NOT NULL
        );
        CREATE INDEX idx_users_email ON users(email);
        """,
    )
    db_path = _create_db(
        tmp_path / "app.db",
        [
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL)",
            "CREATE INDEX idx_users_email ON users(email)",
        ],
    )
    monkeypatch.setattr(sys, "argv", ["drift_db_diff.py", "--doc", str(doc_path), "--db", str(db_path)])

    assert drift_db_diff.main() == 0

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == ["RESULT|ok"]


def test_main_reports_schema_and_index_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    doc_path = _write_design_doc(
        tmp_path / "D-DB.md",
        """
        CREATE TABLE users (
          id INTEGER PRIMARY KEY,
          email TEXT NOT NULL
        );
        CREATE INDEX idx_users_email ON users(email);
        """,
    )
    db_path = _create_db(
        tmp_path / "app.db",
        [
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL, age INTEGER)",
        ],
    )
    monkeypatch.setattr(sys, "argv", ["drift_db_diff.py", "--doc", str(doc_path), "--db", str(db_path)])

    assert drift_db_diff.main() == 0

    output = capsys.readouterr().out
    assert "RESULT|warn" in output
    assert "WARN|schema-drift|table=users: 実 DB のカラム 'age' が設計書にありません" in output
    assert "WARN|index-drift|table=users: 設計書のインデックス 'idx_users_email' が実 DB にありません" in output
