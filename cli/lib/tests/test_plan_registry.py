"""DoD 検証: PLAN-100-unit-test-design.md U-100-001〜005

plan_registry bulk import の回帰を固定する。
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_registry


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_plan_doc(path: Path, *, plan_id: str = "PLAN-100", with_frontmatter: bool = True) -> Path:
    if with_frontmatter:
        path.write_text(
            (
                "---\n"
                f"plan_id: {plan_id}\n"
                f"title: {plan_id} sample\n"
                "kind: design\n"
                "layer: L2\n"
                "drive: be\n"
                "status: draft\n"
                f"created: \"{_timestamp()}\"\n"
                f"revised: \"{_timestamp()}\"\n"
                "---\n\n"
                "# Body\n"
            ),
            encoding="utf-8",
        )
    else:
        path.write_text("# Missing frontmatter\n", encoding="utf-8")
    return path


def _count_rows(db_path: Path, table_name: str) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    finally:
        conn.close()


def test_bulk_import_single(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    db_path = tmp_path / "helix.db"
    _write_plan_doc(docs_dir / "PLAN-100-single.md")

    result = plan_registry.bulk_import(docs_dir=docs_dir, db_path=db_path)

    assert result == {"total": 1, "success": 1, "failed": 0, "errors": []}
    assert _count_rows(db_path, "plan_registry") == 1


def test_bulk_import_all_docs(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"

    result = plan_registry.bulk_import(docs_dir=plan_registry.DEFAULT_DOCS_DIR, db_path=db_path)

    assert result["total"] >= 99
    assert result["success"] >= 99
    assert result["failed"] == 0
    assert _count_rows(db_path, "plan_registry") >= 99


def test_bulk_import_upsert(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    db_path = tmp_path / "helix.db"
    _write_plan_doc(docs_dir / "PLAN-100-upsert.md", plan_id="PLAN-100")

    first = plan_registry.bulk_import(docs_dir=docs_dir, db_path=db_path)
    second = plan_registry.bulk_import(docs_dir=docs_dir, db_path=db_path)

    assert first["success"] == 1
    assert second["success"] == 1
    assert _count_rows(db_path, "plan_registry") == 1


def test_bulk_import_missing_frontmatter(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    db_path = tmp_path / "helix.db"
    _write_plan_doc(docs_dir / "PLAN-100-missing.md", with_frontmatter=False)

    result = plan_registry.bulk_import(docs_dir=docs_dir, db_path=db_path)

    assert result["total"] == 1
    assert result["success"] == 0
    assert result["failed"] == 1
    assert result["errors"] == [f"{(docs_dir / 'PLAN-100-missing.md').as_posix()}: parse_error"]
    assert _count_rows(db_path, "plan_registry") == 0
    assert _count_rows(db_path, "failure_log") == 1


def test_bulk_import_empty_dir(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    db_path = tmp_path / "helix.db"

    result = plan_registry.bulk_import(docs_dir=docs_dir, db_path=db_path)

    assert result == {"total": 0, "success": 0, "failed": 0, "errors": []}
    assert _count_rows(db_path, "plan_registry") == 0
