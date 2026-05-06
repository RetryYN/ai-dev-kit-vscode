import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import code_catalog


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    return db_path


def _git_add(root: Path, *paths: str) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", *paths], cwd=root, check=True, capture_output=True)


def _rebuild_catalog(root: Path) -> Path:
    db_path = root / ".helix" / "helix.db"
    jsonl_path = root / ".helix" / "cache" / "code-catalog.jsonl"
    code_catalog.rebuild_catalog(root, jsonl_path, db_path)
    return db_path


def test_migrate_v16_to_v17_creates_entries_links_tables(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        entry_cols = [row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()]
        link_cols = [row["name"] for row in conn.execute("PRAGMA table_info(links)").fetchall()]
    finally:
        conn.close()

    assert entry_cols == [
        "id",
        "axis",
        "stack",
        "lifecycle",
        "parent_entry_id",
        "sprint_id",
        "agent_actor",
        "ref",
        "version",
        "metadata",
        "created_at",
        "updated_at",
    ]
    assert link_cols == ["from_id", "to_id", "kind", "metadata"]


def test_migrate_v16_to_v17_creates_indexes(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        entry_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(entries)").fetchall()}
        link_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(links)").fetchall()}
    finally:
        conn.close()

    assert {name for name in entry_indexes if name.startswith("idx_entries_")} == {
        "idx_entries_axis",
        "idx_entries_stack",
        "idx_entries_sprint",
        "idx_entries_agent",
        "idx_entries_lifecycle",
    }
    assert {name for name in link_indexes if name.startswith("idx_links_")} == {"idx_links_kind"}


def test_migrate_v16_to_v17_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    helix_db.init_db(db_path)

    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM schema_version WHERE version = 17").fetchone()
    finally:
        conn.close()

    assert row["count"] == 1


def test_entries_axis_check_constraint(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('x', 'invalid', 'initial', 'r')"
            )
    finally:
        conn.close()


def test_links_fk_cascade_on_entry_delete(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('from_x', 'code', 'initial', 'rf')")
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('to_x', 'code', 'initial', 'rt')")
        conn.execute("INSERT INTO links (from_id, to_id, kind) VALUES ('from_x', 'to_x', 'uses')")
        conn.execute("DELETE FROM entries WHERE id = 'from_x'")
        row = conn.execute("SELECT COUNT(*) AS count FROM links").fetchone()
    finally:
        conn.close()

    assert row["count"] == 0


def test_migrate_v17_to_v18_extends_code_index(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        code_index_cols = [row["name"] for row in conn.execute("PRAGMA table_info(code_index)").fetchall()]
    finally:
        conn.close()

    assert code_index_cols == [
        "id",
        "domain",
        "summary",
        "path",
        "line_no",
        "symbol_line",
        "since",
        "related",
        "source_hash",
        "bucket",
        "updated_at",
        "axis",
        "stack",
        "lifecycle",
        "parent_entry_id",
        "sprint_id",
        "agent_actor",
    ]


def test_migrate_v17_to_v18_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    helix_db.init_db(db_path)

    conn = helix_db.get_connection(db_path)
    try:
        version_row = conn.execute("SELECT COUNT(*) AS count FROM schema_version WHERE version = 18").fetchone()
        code_index_cols = [row["name"] for row in conn.execute("PRAGMA table_info(code_index)").fetchall()]
    finally:
        conn.close()

    assert version_row["count"] == 1
    assert len(code_index_cols) == 17


def test_sync_to_db_populates_entries_for_code_axis(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "# @helix:index id=foo.bar domain=cli/lib summary=test\n"
        "def foo():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    _git_add(tmp_path, "sample.py")

    db_path = _rebuild_catalog(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        code_row = conn.execute("SELECT COUNT(*) AS count FROM code_index WHERE id = 'foo.bar'").fetchone()
        entry_row = conn.execute("SELECT axis, lifecycle FROM entries WHERE id = 'foo.bar'").fetchone()
    finally:
        conn.close()

    assert code_row["count"] == 1
    assert entry_row["axis"] == "code"
    assert entry_row["lifecycle"] == "initial"


def test_sync_to_db_respects_lifecycle_field(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "# @helix:index id=foo.baz domain=cli/lib summary=test lifecycle=addition\n"
        "def foo():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    _git_add(tmp_path, "sample.py")

    db_path = _rebuild_catalog(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        entry_row = conn.execute("SELECT lifecycle FROM entries WHERE id = 'foo.baz'").fetchone()
    finally:
        conn.close()

    assert entry_row["lifecycle"] == "addition"
