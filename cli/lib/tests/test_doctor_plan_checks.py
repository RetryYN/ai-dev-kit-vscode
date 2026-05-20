"""DoD 検証: PLAN-093 §5 / U-093-001〜009"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from migrations import v35_plan_registry
import doctor_plan_checks


def _connect_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    v35_plan_registry.migrate_v34_to_v35(conn)
    return conn


def _insert_plan(
    conn: sqlite3.Connection,
    *,
    plan_id: str,
    kind: str = "impl",
    layer: str = "L4",
    status: str = "draft",
    related_adr: str = "",
    updated_at: str = "2026-05-20 00:00:00",
) -> None:
    conn.execute(
        """
        INSERT INTO plan_registry (
            plan_id, title, kind, layer, drive, status, related_adr, frontmatter_json, doc_path, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            plan_id,
            kind,
            layer,
            "be",
            status,
            related_adr,
            "{}",
            f"docs/plans/{plan_id}.md",
            updated_at,
        ),
    )


def _insert_generate(conn: sqlite3.Connection, *, plan_id: str, artifact_path: str, artifact_type: str) -> None:
    conn.execute(
        """
        INSERT INTO plan_generates (plan_id, artifact_path, artifact_type)
        VALUES (?, ?, ?)
        """,
        (plan_id, artifact_path, artifact_type),
    )


def _insert_dependency(conn: sqlite3.Connection, plan_id: str, dep_plan_id: str, dep_type: str = "requires") -> None:
    conn.execute(
        "INSERT INTO plan_dependencies (plan_id, dep_type, dep_plan_id) VALUES (?, ?, ?)",
        (plan_id, dep_type, dep_plan_id),
    )


def test_run_check_plan_drift_marks_existing_artifact_and_updates_exists_check(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    artifact = tmp_path / "cli/lib/doctor_plan_checks.py"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("# ok\n", encoding="utf-8")

    conn = _connect_memory_db()
    try:
        with conn:
            _insert_plan(conn, plan_id="PLAN-093", status="completed")
            _insert_generate(
                conn,
                plan_id="PLAN-093",
                artifact_path="cli/lib/doctor_plan_checks.py",
                artifact_type="python_module",
            )
        rows = doctor_plan_checks.run_check_plan_drift(conn)
        exists_check = conn.execute("SELECT exists_check FROM plan_generates").fetchone()[0]
    finally:
        conn.close()

    assert rows[0]["plan_id"] == "PLAN-093"
    assert rows[0]["artifact_path"] == "cli/lib/doctor_plan_checks.py"
    assert rows[0]["artifact_type"] == "python_module"
    assert rows[0]["status"] == "ok"
    assert rows[0]["reason"] == "ok"
    assert rows[0]["days_stale"] is not None
    assert rows[0]["days_stale"] >= 0
    assert exists_check == 1


def test_run_check_plan_drift_warns_when_artifact_is_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))

    conn = _connect_memory_db()
    try:
        with conn:
            _insert_plan(conn, plan_id="PLAN-093")
            _insert_generate(
                conn,
                plan_id="PLAN-093",
                artifact_path="cli/lib/missing.py",
                artifact_type="python_module",
            )
        rows = doctor_plan_checks.run_check_plan_drift(conn)
        exists_check = conn.execute("SELECT exists_check FROM plan_generates").fetchone()[0]
    finally:
        conn.close()

    assert rows[0]["status"] == "warning"
    assert rows[0]["reason"] == "missing_artifact"
    assert exists_check == 0


def test_run_check_plan_drift_warns_for_stale_active_plan(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    artifact = tmp_path / "docs/plans/PLAN-093.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("# stale\n", encoding="utf-8")

    conn = _connect_memory_db()
    try:
        with conn:
            _insert_plan(conn, plan_id="PLAN-093", status="active", updated_at="2026-04-01 00:00:00")
            _insert_generate(conn, plan_id="PLAN-093", artifact_path="docs/plans/PLAN-093.md", artifact_type="doc")
        rows = doctor_plan_checks.run_check_plan_drift(conn)
    finally:
        conn.close()

    assert rows[0]["status"] == "warning"
    assert rows[0]["reason"] == "stale_generates"
    assert rows[0]["days_stale"] > doctor_plan_checks.STALE_GENERATES_DAYS


def test_run_check_plan_drift_returns_table_warning_when_schema_is_absent() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        rows = doctor_plan_checks.run_check_plan_drift(conn)
    finally:
        conn.close()

    assert rows == [
        {
            "status": "warning",
            "reason": "missing_tables",
            "missing_tables": ["plan_generates", "plan_registry"],
        }
    ]


def test_run_check_plan_cycle_returns_empty_for_acyclic_graph() -> None:
    conn = _connect_memory_db()
    try:
        with conn:
            for plan_id in ("PLAN-091", "PLAN-092", "PLAN-093"):
                _insert_plan(conn, plan_id=plan_id)
            _insert_dependency(conn, "PLAN-091", "PLAN-092")
            _insert_dependency(conn, "PLAN-092", "PLAN-093")
        rows = doctor_plan_checks.run_check_plan_cycle(conn)
    finally:
        conn.close()

    assert rows == []


def test_run_check_plan_cycle_reports_unique_cycle() -> None:
    conn = _connect_memory_db()
    try:
        with conn:
            for plan_id in ("PLAN-091", "PLAN-092", "PLAN-093"):
                _insert_plan(conn, plan_id=plan_id)
            _insert_dependency(conn, "PLAN-091", "PLAN-092")
            _insert_dependency(conn, "PLAN-092", "PLAN-093")
            _insert_dependency(conn, "PLAN-093", "PLAN-091")
        rows = doctor_plan_checks.run_check_plan_cycle(conn)
    finally:
        conn.close()

    assert rows == [
        {
            "plan_id": "PLAN-091",
            "cycle": ["PLAN-091", "PLAN-092", "PLAN-093", "PLAN-091"],
            "status": "warning",
            "reason": "dependency_cycle",
        }
    ]


def test_run_check_plan_adr_snapshot_warns_when_l2_plan_has_no_snapshot() -> None:
    conn = _connect_memory_db()
    try:
        with conn:
            _insert_plan(conn, plan_id="PLAN-091", kind="design", layer="L2")
        rows = doctor_plan_checks.run_check_plan_adr_snapshot(conn)
    finally:
        conn.close()

    assert rows == [
        {
            "plan_id": "PLAN-091",
            "kind": "design",
            "layer": "L2",
            "doc_path": "docs/plans/PLAN-091.md",
            "status": "warning",
            "reason": "missing_adr_snapshot",
        }
    ]


def test_run_check_plan_adr_snapshot_accepts_related_adr_or_snapshot() -> None:
    conn = _connect_memory_db()
    try:
        with conn:
            _insert_plan(conn, plan_id="PLAN-091", kind="design", layer="L2", related_adr="ADR-027")
            _insert_plan(conn, plan_id="PLAN-092", kind="design", layer="L2")
            _insert_generate(
                conn,
                plan_id="PLAN-092",
                artifact_path="docs/adr/ADR-092.md",
                artifact_type="adr_snapshot",
            )
        rows = doctor_plan_checks.run_check_plan_adr_snapshot(conn)
    finally:
        conn.close()

    assert rows == []
