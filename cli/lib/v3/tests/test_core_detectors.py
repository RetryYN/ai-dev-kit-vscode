from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pytest

from cli.lib.v3.detectors.core import (
    CORE_DETECTORS,
    PlanArtifactExpectation,
    PlanArtifactExistenceInput,
    PlanCompletionDriftInput,
    TraceEdge,
    TraceSymmetryInput,
    analyze_plan_artifact_existence,
    analyze_plan_completion_drift,
    analyze_trace_symmetry,
    plan_artifact_existence_messages,
    plan_completion_drift_messages,
    trace_symmetry_messages,
)
from cli.lib.v3.detectors.runner import DetectorSpec, Finding, run_doctor
from cli.lib.v3.schema.ddl import migrate
from cli.lib.v3.projection.upsert import stable_id


@pytest.fixture()
def migrated_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    try:
        yield conn
    finally:
        conn.close()


def _insert_plan(conn: sqlite3.Connection, *, plan_id: str, status: str) -> None:
    conn.execute(
        "INSERT INTO plan_registry(plan_id, kind, layer, sub_doc, drive, status, parent, updated_at, decision_outcome, source_hash) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (plan_id, "impl", "L7", "", "be", status, "", "2026-06-26T00:00:00Z", "", ""),
    )


def _insert_artifact(conn: sqlite3.Connection, *, path: str) -> None:
    conn.execute(
        "INSERT INTO artifact_registry(artifact_id, artifact_type, path, pair_artifact, status, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (
            stable_id("artifact_registry", path),
            "python_module",
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
    edge_kind: str,
    plan_id: str,
) -> None:
    conn.execute(
        "INSERT INTO trace_edges(edge_id, from_artifact, to_artifact, edge_kind, plan_id, status) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (
            stable_id("trace_edges", f"{from_artifact}|{to_artifact}|{edge_kind}"),
            from_artifact,
            to_artifact,
            edge_kind,
            plan_id,
            "active",
        ),
    )


def test_ut_p8_01_analyze_plan_artifact_existence_reports_missing_generated_artifact() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-01"""
    result = analyze_plan_artifact_existence(
        PlanArtifactExistenceInput(
            plan_ids=("PLAN-DET-01",),
            expectations=(
                PlanArtifactExpectation(
                    plan_id="PLAN-DET-01",
                    artifact_path="cli/lib/v3/detectors/core.py",
                    plan_status="draft",
                ),
            ),
            existing_artifact_paths=frozenset(),
        )
    )

    assert result.ok is False
    assert result.missing_sources == ()
    assert plan_artifact_existence_messages(result) == [
        Finding(
            id="FN-DET-01",
            severity="hard",
            subject="PLAN-DET-01",
            missing=("cli/lib/v3/detectors/core.py",),
        )
    ]


def test_ut_p8_02_analyze_plan_artifact_existence_passes_when_all_generated_artifacts_exist() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-02"""
    artifact_path = "cli/lib/v3/detectors/core.py"
    result = analyze_plan_artifact_existence(
        PlanArtifactExistenceInput(
            plan_ids=("PLAN-DET-02",),
            expectations=(
                PlanArtifactExpectation(
                    plan_id="PLAN-DET-02",
                    artifact_path=artifact_path,
                    plan_status="completed",
                ),
            ),
            existing_artifact_paths=frozenset({artifact_path}),
        )
    )

    assert result.ok is True
    assert plan_artifact_existence_messages(result) == []


def test_ut_p8_03_analyze_plan_artifact_existence_fail_closes_when_source_is_absent() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-03"""
    result = analyze_plan_artifact_existence(
        PlanArtifactExistenceInput(
            plan_ids=(),
            expectations=(),
            existing_artifact_paths=frozenset(),
        )
    )

    assert result.ok is False
    assert result.missing_sources == ("plan_registry", "trace_edges.generates")
    assert plan_artifact_existence_messages(result) == [
        Finding(
            id="FN-DET-01",
            severity="hard",
            subject="plan-artifact-existence",
            missing=("plan_registry", "trace_edges.generates"),
        )
    ]


def test_ut_p8_04_analyze_plan_completion_drift_reports_existing_artifact_on_draft_plan() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-04"""
    artifact_path = "cli/lib/v3/detectors/runner.py"
    result = analyze_plan_completion_drift(
        PlanCompletionDriftInput(
            plan_ids=("PLAN-DET-04",),
            expectations=(
                PlanArtifactExpectation(
                    plan_id="PLAN-DET-04",
                    artifact_path=artifact_path,
                    plan_status="draft",
                ),
            ),
            existing_artifact_paths=frozenset({artifact_path}),
        )
    )

    assert result.ok is False
    assert result.missing_sources == ()
    assert plan_completion_drift_messages(result) == [
        Finding(
            id="FN-DET-02",
            severity="hard",
            subject="PLAN-DET-04",
            missing=(artifact_path,),
        )
    ]


def test_ut_p8_05_analyze_plan_completion_drift_passes_when_completed_plan_matches_existing_artifact() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-05"""
    artifact_path = "cli/lib/v3/detectors/runner.py"
    result = analyze_plan_completion_drift(
        PlanCompletionDriftInput(
            plan_ids=("PLAN-DET-05",),
            expectations=(
                PlanArtifactExpectation(
                    plan_id="PLAN-DET-05",
                    artifact_path=artifact_path,
                    plan_status="ready_for_review",
                ),
            ),
            existing_artifact_paths=frozenset({artifact_path}),
        )
    )

    assert result.ok is True
    assert plan_completion_drift_messages(result) == []


def test_ut_p8_06_analyze_plan_completion_drift_fail_closes_when_artifact_source_is_absent() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-06"""
    result = analyze_plan_completion_drift(
        PlanCompletionDriftInput(
            plan_ids=("PLAN-DET-06",),
            expectations=(
                PlanArtifactExpectation(
                    plan_id="PLAN-DET-06",
                    artifact_path="cli/lib/v3/detectors/__init__.py",
                    plan_status="draft",
                ),
            ),
            existing_artifact_paths=frozenset(),
        )
    )

    assert result.ok is False
    assert result.missing_sources == ("artifact_registry",)
    assert plan_completion_drift_messages(result) == [
        Finding(
            id="FN-DET-02",
            severity="hard",
            subject="plan-completion-drift",
            missing=("artifact_registry",),
        )
    ]


def test_ut_p8_07_analyze_trace_symmetry_reports_missing_reverse_edge() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-07"""
    result = analyze_trace_symmetry(
        TraceSymmetryInput(
            edges=(
                TraceEdge(
                    from_artifact="docs/plans/L7/L7-v3-engine-phase8-core-detectorsplan.md",
                    to_artifact="cli/lib/v3/detectors/core.py",
                    edge_kind="generates",
                ),
            )
        )
    )

    assert result.ok is False
    assert result.missing_sources == ()
    assert trace_symmetry_messages(result) == [
        Finding(
            id="FN-DET-03",
            severity="hard",
            subject="docs/plans/L7/L7-v3-engine-phase8-core-detectorsplan.md -> cli/lib/v3/detectors/core.py",
            missing=("cli/lib/v3/detectors/core.py -> docs/plans/L7/L7-v3-engine-phase8-core-detectorsplan.md [generated_by]",),
        )
    ]


def test_ut_p8_08_analyze_trace_symmetry_passes_when_reverse_edge_exists() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-08"""
    result = analyze_trace_symmetry(
        TraceSymmetryInput(
            edges=(
                TraceEdge(
                    from_artifact="docs/plans/L7/L7-v3-engine-phase8-core-detectorsplan.md",
                    to_artifact="cli/lib/v3/detectors/core.py",
                    edge_kind="generates",
                ),
                TraceEdge(
                    from_artifact="cli/lib/v3/detectors/core.py",
                    to_artifact="docs/plans/L7/L7-v3-engine-phase8-core-detectorsplan.md",
                    edge_kind="generated_by",
                ),
            )
        )
    )

    assert result.ok is True
    assert trace_symmetry_messages(result) == []


def test_ut_p8_09_analyze_trace_symmetry_fail_closes_when_source_is_absent() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-09"""
    result = analyze_trace_symmetry(TraceSymmetryInput(edges=()))

    assert result.ok is False
    assert result.missing_sources == ("trace_edges",)
    assert trace_symmetry_messages(result) == [
        Finding(
            id="FN-DET-03",
            severity="hard",
            subject="trace-symmetry",
            missing=("trace_edges",),
        )
    ]


def test_ut_p8_10_run_doctor_uses_and_semantics_without_short_circuit(migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-10"""
    plan_path = "docs/plans/L7/L7-v3-engine-phase8-core-detectorsplan.md"
    artifact_path = "cli/lib/v3/detectors/core.py"

    _insert_plan(migrated_db, plan_id="PLAN-DET-10", status="draft")
    _insert_trace_edge(
        migrated_db,
        from_artifact=plan_path,
        to_artifact=artifact_path,
        edge_kind="generates",
        plan_id="PLAN-DET-10",
    )

    result = run_doctor(migrated_db, CORE_DETECTORS)

    assert result.ok is False
    finding_ids = {finding.id for finding in result.findings}
    # 短絡なし: 先に fail する FN-DET-01 の後でも FN-DET-02/03 が実行され finding を出す
    # (CORE_DETECTORS に detector を足しても壊れない subset 検証)
    assert {"FN-DET-01", "FN-DET-02", "FN-DET-03"} <= finding_ids


@dataclass(frozen=True)
class _FakeResult:
    ok: bool


def test_ut_p8_11_run_doctor_fail_closes_on_loader_error() -> None:
    """DoD 検証: L7-v3-engine-phase8-core-detectorsplan UT-P8-11"""

    def load(_: sqlite3.Connection) -> object:
        raise sqlite3.OperationalError("boom")

    def analyze(_: object) -> _FakeResult:
        return _FakeResult(ok=True)

    def messages(_: _FakeResult) -> list[Finding]:
        return []

    detector = DetectorSpec(
        detector_id="FN-DET-ERR",
        source_kind="db_projection",
        severity="hard",
        load=load,
        analyze=analyze,
        messages=messages,
    )

    conn = sqlite3.connect(":memory:")
    try:
        result = run_doctor(conn, (detector,))
    finally:
        conn.close()

    assert result.ok is False
    assert result.findings == (
        Finding(
            id="FN-DET-ERR",
            severity="hard",
            subject="FN-DET-ERR",
            missing=("boom",),
        ),
    )
