from __future__ import annotations

import sqlite3

from cli.lib.v3.detectors.core import (
    CORE_DETECTORS,
    analyze_plan_dependency,
    load_plan_dependency_input,
    plan_dependency_messages,
)
from cli.lib.v3.projection.upsert import stable_id
from cli.lib.v3.schema.ddl import migrate


def _insert_plan(conn: sqlite3.Connection, *, plan_id: str, status: str = "draft") -> None:
    conn.execute(
        "INSERT INTO plan_registry(plan_id, kind, layer, sub_doc, drive, status, parent, updated_at, decision_outcome, source_hash) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (plan_id, "impl", "L7", "", "be", status, "", "2026-06-27T00:00:00Z", "", ""),
    )


def _insert_requires_edge(conn: sqlite3.Connection, *, from_artifact: str, to_artifact: str) -> None:
    conn.execute(
        "INSERT INTO trace_edges(edge_id, from_artifact, to_artifact, edge_kind, plan_id, status) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (
            stable_id("trace_edges", f"{from_artifact}|{to_artifact}|requires"),
            from_artifact,
            to_artifact,
            "requires",
            from_artifact,
            "active",
        ),
    )


def test_plan_dependency_clean_when_all_required_plans_exist() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_plan(conn, plan_id="PLAN-A")
    _insert_plan(conn, plan_id="PLAN-B")
    _insert_requires_edge(conn, from_artifact="PLAN-A", to_artifact="PLAN-B")

    result = analyze_plan_dependency(load_plan_dependency_input(conn))

    assert result.ok is True
    assert result.missing_sources == ()
    assert result.violations == ()
    assert plan_dependency_messages(result) == []


def test_plan_dependency_flags_single_dangling_requires_edge() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_plan(conn, plan_id="PLAN-A")
    _insert_requires_edge(conn, from_artifact="PLAN-A", to_artifact="PLAN-MISSING")

    result = analyze_plan_dependency(load_plan_dependency_input(conn))

    assert result.ok is False
    assert result.missing_sources == ()
    assert len(result.violations) == 1
    finding = plan_dependency_messages(result)[0]
    assert finding.id == "FN-DET-18"
    assert finding.subject == "PLAN-A requires PLAN-MISSING"
    assert finding.missing == ("missing plan_registry.plan_id: PLAN-MISSING",)


def test_plan_dependency_flags_multiple_dangling_requires_edges() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_plan(conn, plan_id="PLAN-A")
    _insert_plan(conn, plan_id="PLAN-B")
    _insert_requires_edge(conn, from_artifact="PLAN-A", to_artifact="PLAN-X")
    _insert_requires_edge(conn, from_artifact="PLAN-B", to_artifact="PLAN-Y")

    result = analyze_plan_dependency(load_plan_dependency_input(conn))

    assert result.ok is False
    assert tuple(v.to_artifact for v in result.violations) == ("PLAN-X", "PLAN-Y")
    assert [finding.subject for finding in plan_dependency_messages(result)] == [
        "PLAN-A requires PLAN-X",
        "PLAN-B requires PLAN-Y",
    ]


def test_plan_dependency_is_ok_when_no_requires_edges_exist() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_plan(conn, plan_id="PLAN-A")

    result = analyze_plan_dependency(load_plan_dependency_input(conn))

    assert result.ok is True
    assert result.missing_sources == ()
    assert result.violations == ()
    assert plan_dependency_messages(result) == []


def test_plan_dependency_detector_is_registered_in_core_registry() -> None:
    assert "FN-DET-18" in {spec.detector_id for spec in CORE_DETECTORS}
