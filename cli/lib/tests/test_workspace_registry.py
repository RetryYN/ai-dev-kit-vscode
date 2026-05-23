from __future__ import annotations

import sqlite3

import pytest

from cli.lib import helix_db


def _conn_with_v35_baseline() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (35, datetime('now'))"
    )
    conn.commit()
    return conn


def test_migrate_v35_to_v36_is_idempotent() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db._migrate_v35_to_v36(conn)
        helix_db._migrate_v35_to_v36(conn)
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(workspace_registry)")]
        indexes = {
            row["name"] for row in conn.execute("PRAGMA index_list(workspace_registry)").fetchall()
        }
    finally:
        conn.close()

    assert "task_id" in columns
    assert "status" in columns
    assert "idx_workspace_registry_status" in indexes
    assert "idx_workspace_registry_task_id" in indexes


def test_migrate_promotes_schema_to_36() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        conn.close()

    assert version == 36


def test_workspace_registry_insert_and_get_roundtrip() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        row_id = helix_db.workspace_registry_insert(
            conn,
            task_id="PLAN-156",
            workspace_path="/tmp/ws/plan-156",
            branch="workspace/PLAN-156",
            base_sha="abc123",
            reserved_resources={"ports": [8000]},
        )
        row = helix_db.workspace_registry_get(conn, "PLAN-156")
    finally:
        conn.close()

    assert row_id > 0
    assert row is not None
    assert row["task_id"] == "PLAN-156"
    assert row["reserved_resources"] == {"ports": [8000]}


def test_workspace_registry_insert_duplicate_task_id_raises_integrity_error() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        helix_db.workspace_registry_insert(
            conn,
            task_id="WBS-003",
            workspace_path="/tmp/ws/wbs-003",
            branch="workspace/WBS-003",
            base_sha="sha1",
        )
        with pytest.raises(sqlite3.IntegrityError):
            helix_db.workspace_registry_insert(
                conn,
                task_id="WBS-003",
                workspace_path="/tmp/ws/wbs-003-2",
                branch="workspace/WBS-003-2",
                base_sha="sha2",
            )
    finally:
        conn.close()


def test_workspace_registry_get_returns_none_for_missing_task() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        row = helix_db.workspace_registry_get(conn, "PLAN-NOT-FOUND")
    finally:
        conn.close()

    assert row is None


def test_workspace_registry_list_filters_by_status() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        helix_db.workspace_registry_insert(
            conn,
            task_id="A",
            workspace_path="/tmp/ws/A",
            branch="workspace/A",
            base_sha="shaA",
        )
        helix_db.workspace_registry_insert(
            conn,
            task_id="B",
            workspace_path="/tmp/ws/B",
            branch="workspace/B",
            base_sha="shaB",
        )
        updated = helix_db.workspace_registry_update_status(
            conn,
            "B",
            status="dropped",
            drop_reason="abort",
        )
        active_rows = helix_db.workspace_registry_list(conn, status="active")
        dropped_rows = helix_db.workspace_registry_list(conn, status="dropped")
    finally:
        conn.close()

    assert updated is True
    assert [row["task_id"] for row in active_rows] == ["A"]
    assert [row["task_id"] for row in dropped_rows] == ["B"]


def test_workspace_registry_update_status_records_drop_metadata() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        helix_db.workspace_registry_insert(
            conn,
            task_id="DROP-1",
            workspace_path="/tmp/ws/drop1",
            branch="workspace/DROP-1",
            base_sha="shaD1",
        )
        updated = helix_db.workspace_registry_update_status(
            conn,
            "DROP-1",
            status="dropped",
            drop_reason="force",
        )
        row = helix_db.workspace_registry_get(conn, "DROP-1")
    finally:
        conn.close()

    assert updated is True
    assert row is not None
    assert row["status"] == "dropped"
    assert row["drop_reason"] == "force"
    assert row["dropped_at"] != ""


def test_workspace_registry_update_status_returns_false_for_missing_task() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        updated = helix_db.workspace_registry_update_status(
            conn,
            "NO-TASK",
            status="merged",
        )
    finally:
        conn.close()

    assert updated is False


def test_workspace_registry_status_check_constraint_violation_raises_integrity_error() -> None:
    conn = _conn_with_v35_baseline()
    try:
        helix_db.migrate(conn)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO workspace_registry (
                    task_id, workspace_path, branch, base_sha, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                ("BAD-STATUS", "/tmp/ws/bad", "workspace/BAD", "shaBAD", "invalid"),
            )
    finally:
        conn.close()
