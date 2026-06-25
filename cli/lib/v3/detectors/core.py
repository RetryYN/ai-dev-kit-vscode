from __future__ import annotations

import sqlite3
from dataclasses import dataclass

try:
    from v3.schema import registry
except ImportError:  # pragma: no cover - repo-local fallback until top-level v3 package is wired.
    from cli.lib.v3.schema import registry

from .runner import DetectorSpec, Finding

FN_DET_01 = "FN-DET-01"
FN_DET_02 = "FN-DET-02"
FN_DET_03 = "FN-DET-03"
HARD = "hard"
DB_PROJECTION = "db_projection"

REVERSE_EDGE_KIND = {
    "generated_by": "generates",
    "generates": "generated_by",
    "pairs_with": "pairs_with",
    "required_by": "requires",
    "requires": "required_by",
}


@dataclass(frozen=True)
class PlanArtifactExpectation:
    plan_id: str
    artifact_path: str
    plan_status: str


@dataclass(frozen=True)
class PlanArtifactViolation:
    plan_id: str
    artifact_path: str


@dataclass(frozen=True)
class PlanArtifactExistenceInput:
    plan_ids: tuple[str, ...]
    expectations: tuple[PlanArtifactExpectation, ...]
    existing_artifact_paths: frozenset[str]


@dataclass(frozen=True)
class PlanArtifactExistenceResult:
    ok: bool
    missing_sources: tuple[str, ...]
    violations: tuple[PlanArtifactViolation, ...]


@dataclass(frozen=True)
class PlanCompletionDriftInput:
    plan_ids: tuple[str, ...]
    expectations: tuple[PlanArtifactExpectation, ...]
    existing_artifact_paths: frozenset[str]


@dataclass(frozen=True)
class PlanCompletionDriftResult:
    ok: bool
    missing_sources: tuple[str, ...]
    violations: tuple[PlanArtifactViolation, ...]


@dataclass(frozen=True)
class TraceEdge:
    from_artifact: str
    to_artifact: str
    edge_kind: str


@dataclass(frozen=True)
class MissingReverseEdge:
    from_artifact: str
    to_artifact: str
    reverse_kind: str


@dataclass(frozen=True)
class TraceSymmetryInput:
    edges: tuple[TraceEdge, ...]


@dataclass(frozen=True)
class TraceSymmetryResult:
    ok: bool
    missing_sources: tuple[str, ...]
    violations: tuple[MissingReverseEdge, ...]


def _table_columns(table_name: str) -> set[str]:
    return {column.name for column in registry.TABLE_BY_NAME[table_name].columns}


def _ensure_table_columns(table_name: str, required_columns: tuple[str, ...]) -> None:
    available = _table_columns(table_name)
    missing = tuple(column for column in required_columns if column not in available)
    if missing:
        raise ValueError(f"{table_name} missing columns: {', '.join(missing)}")


def _load_plan_ids(db: sqlite3.Connection) -> tuple[str, ...]:
    _ensure_table_columns("plan_registry", ("plan_id",))
    rows = db.execute("SELECT plan_id FROM plan_registry ORDER BY plan_id").fetchall()
    return tuple(row[0] for row in rows if row[0])


def _load_plan_artifact_expectations(db: sqlite3.Connection) -> tuple[PlanArtifactExpectation, ...]:
    _ensure_table_columns("plan_registry", ("plan_id", "status"))
    _ensure_table_columns("trace_edges", ("plan_id", "to_artifact", "edge_kind"))
    rows = db.execute(
        "SELECT e.plan_id, e.to_artifact, p.status "
        "FROM trace_edges AS e "
        "JOIN plan_registry AS p ON p.plan_id = e.plan_id "
        "WHERE e.edge_kind = 'generates' "
        "ORDER BY e.plan_id, e.to_artifact"
    ).fetchall()
    return tuple(
        PlanArtifactExpectation(
            plan_id=row[0],
            artifact_path=row[1],
            plan_status=row[2],
        )
        for row in rows
        if row[0] and row[1]
    )


def _load_existing_artifact_paths(db: sqlite3.Connection) -> frozenset[str]:
    _ensure_table_columns("artifact_registry", ("path",))
    rows = db.execute("SELECT path FROM artifact_registry ORDER BY path").fetchall()
    return frozenset(row[0] for row in rows if row[0])


def load_plan_artifact_existence_input(db: sqlite3.Connection) -> PlanArtifactExistenceInput:
    return PlanArtifactExistenceInput(
        plan_ids=_load_plan_ids(db),
        expectations=_load_plan_artifact_expectations(db),
        existing_artifact_paths=_load_existing_artifact_paths(db),
    )


def load_plan_completion_drift_input(db: sqlite3.Connection) -> PlanCompletionDriftInput:
    return PlanCompletionDriftInput(
        plan_ids=_load_plan_ids(db),
        expectations=_load_plan_artifact_expectations(db),
        existing_artifact_paths=_load_existing_artifact_paths(db),
    )


def load_trace_symmetry_input(db: sqlite3.Connection) -> TraceSymmetryInput:
    _ensure_table_columns("trace_edges", ("from_artifact", "to_artifact", "edge_kind"))
    rows = db.execute(
        "SELECT from_artifact, to_artifact, edge_kind "
        "FROM trace_edges ORDER BY from_artifact, to_artifact, edge_kind"
    ).fetchall()
    return TraceSymmetryInput(
        edges=tuple(
            TraceEdge(
                from_artifact=row[0],
                to_artifact=row[1],
                edge_kind=row[2],
            )
            for row in rows
            if row[0] and row[1] and row[2]
        )
    )


def analyze_plan_artifact_existence(input_data: PlanArtifactExistenceInput) -> PlanArtifactExistenceResult:
    missing_sources: list[str] = []
    if not input_data.plan_ids:
        missing_sources.append("plan_registry")
    if not input_data.expectations:
        missing_sources.append("trace_edges.generates")
    if missing_sources:
        return PlanArtifactExistenceResult(
            ok=False,
            missing_sources=tuple(missing_sources),
            violations=(),
        )

    violations = tuple(
        PlanArtifactViolation(
            plan_id=expectation.plan_id,
            artifact_path=expectation.artifact_path,
        )
        for expectation in input_data.expectations
        if expectation.artifact_path not in input_data.existing_artifact_paths
    )
    return PlanArtifactExistenceResult(
        ok=not violations,
        missing_sources=(),
        violations=violations,
    )


def analyze_plan_completion_drift(input_data: PlanCompletionDriftInput) -> PlanCompletionDriftResult:
    missing_sources: list[str] = []
    if not input_data.plan_ids:
        missing_sources.append("plan_registry")
    if not input_data.expectations:
        missing_sources.append("trace_edges.generates")
    if not input_data.existing_artifact_paths:
        missing_sources.append("artifact_registry")
    if missing_sources:
        return PlanCompletionDriftResult(
            ok=False,
            missing_sources=tuple(missing_sources),
            violations=(),
        )

    violations = tuple(
        PlanArtifactViolation(
            plan_id=expectation.plan_id,
            artifact_path=expectation.artifact_path,
        )
        for expectation in input_data.expectations
        if expectation.plan_status == "draft" and expectation.artifact_path in input_data.existing_artifact_paths
    )
    return PlanCompletionDriftResult(
        ok=not violations,
        missing_sources=(),
        violations=violations,
    )


def analyze_trace_symmetry(input_data: TraceSymmetryInput) -> TraceSymmetryResult:
    if not input_data.edges:
        return TraceSymmetryResult(
            ok=False,
            missing_sources=("trace_edges",),
            violations=(),
        )

    edge_index = {
        (edge.from_artifact, edge.to_artifact, edge.edge_kind)
        for edge in input_data.edges
    }
    violations = tuple(
        MissingReverseEdge(
            from_artifact=edge.from_artifact,
            to_artifact=edge.to_artifact,
            reverse_kind=REVERSE_EDGE_KIND.get(edge.edge_kind, edge.edge_kind),
        )
        for edge in input_data.edges
        if (
            edge.to_artifact,
            edge.from_artifact,
            REVERSE_EDGE_KIND.get(edge.edge_kind, edge.edge_kind),
        )
        not in edge_index
    )
    return TraceSymmetryResult(
        ok=not violations,
        missing_sources=(),
        violations=violations,
    )


def _absence_finding(detector_id: str, subject: str, missing_sources: tuple[str, ...]) -> Finding:
    return Finding(
        id=detector_id,
        severity=HARD,
        subject=subject,
        missing=missing_sources,
    )


def plan_artifact_existence_messages(result: PlanArtifactExistenceResult) -> list[Finding]:
    if result.missing_sources:
        return [_absence_finding(FN_DET_01, "plan-artifact-existence", result.missing_sources)]
    return [
        Finding(
            id=FN_DET_01,
            severity=HARD,
            subject=violation.plan_id,
            missing=(violation.artifact_path,),
        )
        for violation in result.violations
    ]


def plan_completion_drift_messages(result: PlanCompletionDriftResult) -> list[Finding]:
    if result.missing_sources:
        return [_absence_finding(FN_DET_02, "plan-completion-drift", result.missing_sources)]
    return [
        Finding(
            id=FN_DET_02,
            severity=HARD,
            subject=violation.plan_id,
            missing=(violation.artifact_path,),
        )
        for violation in result.violations
    ]


def trace_symmetry_messages(result: TraceSymmetryResult) -> list[Finding]:
    if result.missing_sources:
        return [_absence_finding(FN_DET_03, "trace-symmetry", result.missing_sources)]
    return [
        Finding(
            id=FN_DET_03,
            severity=HARD,
            subject=f"{violation.from_artifact} -> {violation.to_artifact}",
            missing=(
                f"{violation.to_artifact} -> {violation.from_artifact} [{violation.reverse_kind}]",
            ),
        )
        for violation in result.violations
    ]


CORE_DETECTORS = (
    DetectorSpec(
        detector_id=FN_DET_01,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_plan_artifact_existence_input,
        analyze=analyze_plan_artifact_existence,
        messages=plan_artifact_existence_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_02,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_plan_completion_drift_input,
        analyze=analyze_plan_completion_drift,
        messages=plan_completion_drift_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_03,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_trace_symmetry_input,
        analyze=analyze_trace_symmetry,
        messages=trace_symmetry_messages,
    ),
)
