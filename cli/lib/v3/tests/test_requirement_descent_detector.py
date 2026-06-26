from __future__ import annotations

import sqlite3

from cli.lib.v3.detectors.core import (
    analyze_requirement_descent,
    load_requirement_descent_input,
    requirement_descent_messages,
)
from cli.lib.v3.projection.upsert import stable_id
from cli.lib.v3.schema.ddl import migrate


def _insert_functional(conn: sqlite3.Connection, *, fn_id: str, layer: str = "L4_required") -> None:
    conn.execute(
        "INSERT INTO functional_registry(fn_id, fr_id, layer, maps_to, registry_hash) VALUES(?, ?, ?, ?, ?)",
        (fn_id, "", layer, "", "hash"),
    )


def _insert_artifact(conn: sqlite3.Connection, *, path: str, artifact_type: str = "design_doc") -> None:
    conn.execute(
        "INSERT INTO artifact_registry(artifact_id, artifact_type, path, pair_artifact, status, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (
            stable_id("artifact_registry", path),
            artifact_type,
            path,
            "",
            "active",
            "2026-06-26T00:00:00Z",
        ),
    )


def _insert_trace_edge(
    conn: sqlite3.Connection,
    *,
    from_artifact: str,
    to_artifact: str,
    edge_kind: str = "requires",
) -> None:
    conn.execute(
        "INSERT INTO trace_edges(edge_id, from_artifact, to_artifact, edge_kind, plan_id, status) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (
            stable_id("trace_edges", f"{from_artifact}|{to_artifact}|{edge_kind}"),
            from_artifact,
            to_artifact,
            edge_kind,
            "PLAN-DET-04",
            "active",
        ),
    )


def _insert_test_case(conn: sqlite3.Connection, *, test_name: str, fr_id: str) -> None:
    conn.execute(
        "INSERT INTO test_cases("
        "test_case_id, test_run_id, test_file, test_name, plan_id, fr_id, artifact_id, kind, oracle_id, "
        "name, first_seen_at, last_seen_at, status, duration_ms, evidence_path"
        ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            stable_id("test_cases", test_name),
            "",
            "cli/lib/v3/tests/test_requirement_descent_detector.py",
            test_name,
            "",
            fr_id,
            "",
            "unit",
            "",
            test_name,
            "",
            "",
            "discovered",
            0.0,
            "cli/lib/v3/tests/test_requirement_descent_detector.py",
        ),
    )


def test_requirement_descent_clean_when_design_and_test_are_reachable() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_functional(conn, fn_id="FR-A-001")
    _insert_artifact(conn, path="docs/v2/L6-design/FR-A-001.md")
    _insert_trace_edge(conn, from_artifact="FR-A-001", to_artifact="docs/v2/L6-design/FR-A-001.md")
    _insert_test_case(conn, test_name="test_fr_a_001", fr_id="FR-A-001")

    result = analyze_requirement_descent(load_requirement_descent_input(conn))

    assert result.ok is True
    assert result.missing_design_fr_ids == ()
    assert result.missing_test_fr_ids == ()
    assert requirement_descent_messages(result) == []


def test_requirement_descent_flags_fr_without_design_reachability() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_functional(conn, fn_id="FR-B-001")
    _insert_test_case(conn, test_name="test_fr_b_001", fr_id="FR-B-001")

    result = analyze_requirement_descent(load_requirement_descent_input(conn))

    assert result.ok is False
    assert result.missing_design_fr_ids == ("FR-B-001",)
    assert result.missing_test_fr_ids == ()
    finding = requirement_descent_messages(result)[0]
    assert finding.subject == "FR-B-001"
    assert finding.missing == ("no reachable design artifact via trace_edges",)


def test_requirement_descent_flags_fr_without_downstream_test_case() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    _insert_functional(conn, fn_id="FR-C-001")
    _insert_artifact(conn, path="docs/v2/L5-design/FR-C-001.md")
    _insert_trace_edge(conn, from_artifact="FR-C-001", to_artifact="docs/v2/L5-design/FR-C-001.md")

    result = analyze_requirement_descent(load_requirement_descent_input(conn))

    assert result.ok is False
    assert result.missing_design_fr_ids == ()
    assert result.missing_test_fr_ids == ("FR-C-001",)
    finding = requirement_descent_messages(result)[0]
    assert finding.subject == "FR-C-001"
    assert finding.missing == ("design reachable but no downstream test_cases",)


def test_requirement_descent_is_ok_when_no_fr_targets_exist() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)

    result = analyze_requirement_descent(load_requirement_descent_input(conn))

    assert result.ok is True
    assert result.missing_design_fr_ids == ()
    assert result.missing_test_fr_ids == ()
    assert requirement_descent_messages(result) == []
