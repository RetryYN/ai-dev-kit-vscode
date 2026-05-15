import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _build_v22_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.executescript(helix_db.DESIGN_SPRINT_ENTRIES_SCHEMA_V21)
    conn.executescript(helix_db.DESIGN_SPRINT_ARTIFACT_LINKS_SCHEMA_V21)
    helix_db._migrate_v21_to_v22(conn)
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (22, '2026-05-15T00:00:00')"
    )
    conn.commit()
    return conn


def _insert_entry(
    conn: sqlite3.Connection,
    *,
    plan_id: str = "PLAN-068",
    sprint_id: str | None = "W-3",
    sprint_type: str = "functional",
    layer: str = "functional",
    drive: str = "be",
    track: str = "be",
    pair_status: str = "pending",
    raw_meta: str = '{"scope":"default"}',
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO design_sprint_entries (
            plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, raw_meta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, raw_meta),
    )
    return int(cursor.lastrowid)


def _insert_artifact_link(
    conn: sqlite3.Connection,
    *,
    sprint_entry_id: int,
    artifact_kind: str = "design",
    artifact_ref: str = "docs/features/PLAN-068/v1.md",
    link_kind: str = "covers",
) -> int:
    conn.execute(
        """
        INSERT INTO design_sprint_artifact_links (
            sprint_entry_id, artifact_kind, artifact_ref, link_kind
        ) VALUES (?, ?, ?, ?)
        """,
        (sprint_entry_id, artifact_kind, artifact_ref, link_kind),
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def test_v22_to_v23_migrate_succeeds(tmp_path: Path) -> None:
    conn = _build_v22_db(tmp_path / "legacy-v22.db")
    try:
        helix_db.migrate(conn)
        entry_columns = {row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()}
        link_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_artifact_links)").fetchall()
        }
        max_version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        conn.close()

    assert {"supersedes_entry_id", "correction_reason", "voided_at"} <= entry_columns
    assert {"supersedes_entry_id", "correction_reason", "voided_at"} <= link_columns
    assert max_version == helix_db.CURRENT_SCHEMA_VERSION


def test_v23_to_v23_migrate_is_idempotent(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    conn = helix_db.get_connection(db_path)
    try:
        helix_db.migrate(conn)
        versions = conn.execute("SELECT version FROM schema_version WHERE version = 23").fetchall()
        entry_columns = [row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_entries)").fetchall()]
        link_columns = [row["name"] for row in conn.execute("PRAGMA table_info(design_sprint_artifact_links)").fetchall()]
    finally:
        conn.close()

    assert len(versions) == 1
    assert entry_columns.count("supersedes_entry_id") == 1
    assert entry_columns.count("correction_reason") == 1
    assert entry_columns.count("voided_at") == 1
    assert link_columns.count("supersedes_entry_id") == 1
    assert link_columns.count("correction_reason") == 1
    assert link_columns.count("voided_at") == 1


def test_void_entry_with_correction_voids_old_and_appends_new(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    conn = helix_db.get_connection(db_path)
    try:
        old_entry_id = _insert_entry(conn, pair_status="design_only", raw_meta='{"scope":"legacy"}')
        new_entry_id = helix_db.void_entry_with_correction(
            conn,
            old_entry_id,
            {"drive": "fe", "pair_status": "paired", "raw_meta": '{"scope":"corrected"}'},
            "wrong drive recorded",
        )
        conn.commit()
        rows = conn.execute(
            """
            SELECT id, drive, pair_status, raw_meta, supersedes_entry_id, correction_reason, voided_at
            FROM design_sprint_entries
            ORDER BY id
            """
        ).fetchall()
    finally:
        conn.close()

    assert [row["id"] for row in rows] == [old_entry_id, new_entry_id]
    assert rows[0]["voided_at"] is not None
    assert rows[1]["drive"] == "fe"
    assert rows[1]["pair_status"] == "paired"
    assert rows[1]["raw_meta"] == '{"scope":"corrected"}'
    assert rows[1]["supersedes_entry_id"] == old_entry_id
    assert rows[1]["correction_reason"] == "wrong drive recorded"
    assert rows[1]["voided_at"] is None


def test_void_entry_with_correction_rolls_back_on_invalid_payload(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    conn = helix_db.get_connection(db_path)
    try:
        old_entry_id = _insert_entry(conn)
        with pytest.raises(ValueError, match="invalid drive"):
            helix_db.void_entry_with_correction(
                conn,
                old_entry_id,
                {"drive": "invalid"},
                "bad correction payload",
            )
        rows = conn.execute(
            "SELECT id, voided_at FROM design_sprint_entries WHERE plan_id = ? ORDER BY id",
            ("PLAN-068",),
        ).fetchall()
    finally:
        conn.close()

    assert [row["id"] for row in rows] == [old_entry_id]
    assert rows[0]["voided_at"] is None


def test_list_active_entries_excludes_voided_rows(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    conn = helix_db.get_connection(db_path)
    try:
        old_entry_id = _insert_entry(conn)
        new_entry_id = helix_db.void_entry_with_correction(
            conn,
            old_entry_id,
            {"drive": "db", "track": "db"},
            "move corrected entry to db drive",
        )
        second_active_id = _insert_entry(conn, sprint_id="W-3b", drive="fullstack", track="shared")
        conn.commit()
        active_rows = helix_db.list_active_entries(conn, "PLAN-068", "functional", "functional")
    finally:
        conn.close()

    assert [row["id"] for row in active_rows] == [new_entry_id, second_active_id]


def test_void_artifact_link_with_correction_voids_old_and_appends_new(tmp_path: Path, capsys) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    conn = helix_db.get_connection(db_path)
    try:
        sprint_entry_id = _insert_entry(conn)
        old_link_rowid = _insert_artifact_link(conn, sprint_entry_id=sprint_entry_id)
        new_link_rowid = helix_db.void_artifact_link_with_correction(
            conn,
            old_link_rowid,
            {"artifact_ref": "docs/features/PLAN-068/v2.md"},
            "artifact path corrected",
        )
        conn.commit()
        rows = conn.execute(
            """
            SELECT rowid AS link_rowid, sprint_entry_id, artifact_ref,
                   supersedes_entry_id, correction_reason, voided_at
            FROM design_sprint_artifact_links
            ORDER BY link_rowid
            """
        ).fetchall()
    finally:
        conn.close()

    assert [row["link_rowid"] for row in rows] == [old_link_rowid, new_link_rowid]
    assert rows[0]["voided_at"] is not None
    assert rows[1]["artifact_ref"] == "docs/features/PLAN-068/v2.md"
    assert rows[1]["supersedes_entry_id"] == sprint_entry_id
    assert rows[1]["correction_reason"] == "artifact path corrected"
    assert rows[1]["voided_at"] is None
