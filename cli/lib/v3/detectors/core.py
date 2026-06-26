from __future__ import annotations

import os
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


FN_DET_11 = "FN-DET-11"
FN_DET_12 = "FN-DET-12"

KEY_PROJECTION_TABLES = ("plan_registry", "artifact_registry", "test_cases", "trace_edges")


@dataclass(frozen=True)
class DbProjectionCoverageInput:
    table_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class DbProjectionCoverageResult:
    ok: bool
    empty_tables: tuple[str, ...]


def load_db_projection_coverage_input(db: sqlite3.Connection) -> DbProjectionCoverageInput:
    counts: list[tuple[str, int]] = []
    for table_name in KEY_PROJECTION_TABLES:
        # table_name は固定 allowlist 由来（injection なし）。registry 実在も確認。
        _ensure_table_columns(table_name, ())
        count = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        counts.append((table_name, int(count)))
    return DbProjectionCoverageInput(table_counts=tuple(counts))


def analyze_db_projection_coverage(input_data: DbProjectionCoverageInput) -> DbProjectionCoverageResult:
    # absence=ok=false: key projection table が空（0 行）= もれ
    empty = tuple(table for table, count in input_data.table_counts if count == 0)
    return DbProjectionCoverageResult(ok=not empty, empty_tables=empty)


def db_projection_coverage_messages(result: DbProjectionCoverageResult) -> list[Finding]:
    return [
        Finding(id=FN_DET_11, severity=HARD, subject="db-projection-coverage", missing=(table,))
        for table in result.empty_tables
    ]


@dataclass(frozen=True)
class SchemaSsotInput:
    db_tables: frozenset[str]
    registry_tables: frozenset[str]


@dataclass(frozen=True)
class SchemaSsotResult:
    ok: bool
    rogue_tables: tuple[str, ...]
    missing_tables: tuple[str, ...]


def load_schema_ssot_input(db: sqlite3.Connection) -> SchemaSsotInput:
    db_tables = frozenset(
        row[0]
        for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if row[0] and not row[0].startswith("sqlite_")
    )
    registry_tables = frozenset(table.name for table in registry.TABLES)
    return SchemaSsotInput(db_tables=db_tables, registry_tables=registry_tables)


def analyze_schema_ssot(input_data: SchemaSsotInput) -> SchemaSsotResult:
    # registry 外 table（rogue）/ registry にあるが DB 未作成（missing）= 違反。absence(db 空)も missing で ok=false。
    rogue = tuple(sorted(input_data.db_tables - input_data.registry_tables))
    missing = tuple(sorted(input_data.registry_tables - input_data.db_tables))
    return SchemaSsotResult(ok=not rogue and not missing, rogue_tables=rogue, missing_tables=missing)


def schema_ssot_messages(result: SchemaSsotResult) -> list[Finding]:
    findings: list[Finding] = []
    for table in result.rogue_tables:
        findings.append(Finding(id=FN_DET_12, severity=HARD, subject="schema-ssot.rogue-table", missing=(table,)))
    for table in result.missing_tables:
        findings.append(Finding(id=FN_DET_12, severity=HARD, subject="schema-ssot.missing-table", missing=(table,)))
    return findings


FN_DET_10 = "FN-DET-10"
FILE_SNAPSHOT = "file_snapshot"
VALID_SOURCE_KINDS = frozenset({DB_PROJECTION, FILE_SNAPSHOT, "hybrid"})
VALID_SEVERITIES = frozenset({HARD, "advisory", "soft"})


@dataclass(frozen=True)
class LintWiringInput:
    detector_ids: tuple[str, ...]
    source_kinds: tuple[str, ...]
    severities: tuple[str, ...]


@dataclass(frozen=True)
class LintWiringResult:
    ok: bool
    duplicate_ids: tuple[str, ...]
    invalid_source_kinds: tuple[str, ...]
    invalid_severities: tuple[str, ...]


def load_lint_wiring_input(db: sqlite3.Connection) -> LintWiringInput:
    # CORE_DETECTORS = 本 module の detector registry。C4 死蔵防止メタゲート(registry の形式健全性)。
    specs = CORE_DETECTORS
    return LintWiringInput(
        detector_ids=tuple(spec.detector_id for spec in specs),
        source_kinds=tuple(spec.source_kind for spec in specs),
        severities=tuple(spec.severity for spec in specs),
    )


def analyze_lint_wiring(input_data: LintWiringInput) -> LintWiringResult:
    if not input_data.detector_ids:  # absence=ok=false: 空 registry
        return LintWiringResult(
            ok=False, duplicate_ids=(), invalid_source_kinds=("<empty-registry>",), invalid_severities=()
        )
    counts: dict[str, int] = {}
    for detector_id in input_data.detector_ids:
        counts[detector_id] = counts.get(detector_id, 0) + 1
    duplicate = tuple(sorted(d for d, n in counts.items() if n > 1))
    invalid_sk = tuple(sorted({sk for sk in input_data.source_kinds if sk not in VALID_SOURCE_KINDS}))
    invalid_sev = tuple(sorted({sv for sv in input_data.severities if sv not in VALID_SEVERITIES}))
    return LintWiringResult(
        ok=not duplicate and not invalid_sk and not invalid_sev,
        duplicate_ids=duplicate,
        invalid_source_kinds=invalid_sk,
        invalid_severities=invalid_sev,
    )


def lint_wiring_messages(result: LintWiringResult) -> list[Finding]:
    findings: list[Finding] = []
    for detector_id in result.duplicate_ids:
        findings.append(Finding(id=FN_DET_10, severity=HARD, subject="lint-wiring.duplicate-id", missing=(detector_id,)))
    for source_kind in result.invalid_source_kinds:
        findings.append(Finding(id=FN_DET_10, severity=HARD, subject="lint-wiring.invalid-source-kind", missing=(source_kind,)))
    for severity in result.invalid_severities:
        findings.append(Finding(id=FN_DET_10, severity=HARD, subject="lint-wiring.invalid-severity", missing=(severity,)))
    return findings


FN_DET_14 = "FN-DET-14"
VALID_MANIFEST_SCOPES = frozenset({"common", "claude", "codex"})
# core.py = cli/lib/v3/detectors/core.py → repo root は dirname×5。
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)


@dataclass(frozen=True)
class ManifestRow:
    scope: str
    import_path: str
    raw: str


@dataclass(frozen=True)
class DistApiInput:
    manifest_present: bool
    rows: tuple[ManifestRow, ...]


@dataclass(frozen=True)
class DistApiResult:
    ok: bool
    missing_manifest: bool
    invalid_rows: tuple[str, ...]


def load_dist_api_input(db: sqlite3.Connection) -> DistApiInput:
    # source_kind=file_snapshot: loader が core-manifest.tsv の読取を隔離(analyze は pure)。
    manifest_path = os.path.join(_REPO_ROOT, "helix", "core-manifest.tsv")
    if not os.path.isfile(manifest_path):
        return DistApiInput(manifest_present=False, rows=())
    rows: list[ManifestRow] = []
    with open(manifest_path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.rstrip("\n")
            if not stripped.strip() or stripped.lstrip().startswith("#"):
                continue
            parts = stripped.split("\t")
            rows.append(
                ManifestRow(
                    scope=parts[0].strip() if parts else "",
                    import_path=parts[1].strip() if len(parts) > 1 else "",
                    raw=stripped,
                )
            )
    return DistApiInput(manifest_present=True, rows=tuple(rows))


def analyze_dist_api(input_data: DistApiInput) -> DistApiResult:
    if not input_data.manifest_present:  # absence=ok=false
        return DistApiResult(ok=False, missing_manifest=True, invalid_rows=())
    if not input_data.rows:
        return DistApiResult(ok=False, missing_manifest=False, invalid_rows=("<empty-manifest>",))
    invalid = tuple(
        row.raw
        for row in input_data.rows
        if row.scope not in VALID_MANIFEST_SCOPES
        or not row.import_path.startswith("@~/.helix/core/")
    )
    return DistApiResult(ok=not invalid, missing_manifest=False, invalid_rows=invalid)


def dist_api_messages(result: DistApiResult) -> list[Finding]:
    findings: list[Finding] = []
    if result.missing_manifest:
        findings.append(
            Finding(id=FN_DET_14, severity=HARD, subject="dist-api.manifest-missing", missing=("helix/core-manifest.tsv",))
        )
    for raw in result.invalid_rows:
        findings.append(Finding(id=FN_DET_14, severity=HARD, subject="dist-api.invalid-row", missing=(raw,)))
    return findings


FN_DET_08 = "FN-DET-08"


@dataclass(frozen=True)
class DrivePassageInput:
    drive_plan_ids: tuple[str, ...]
    forward_return_plan_ids: frozenset[str]


@dataclass(frozen=True)
class DrivePassageResult:
    ok: bool
    missing_forward_return: tuple[str, ...]


def load_drive_passage_input(db: sqlite3.Connection) -> DrivePassageInput:
    _ensure_table_columns("drive_runs", ("plan_id",))
    _ensure_table_columns("trace_edges", ("from_artifact", "edge_kind"))
    drive_plans = tuple(
        row[0] for row in db.execute("SELECT plan_id FROM drive_runs ORDER BY plan_id").fetchall() if row[0]
    )
    forward_return_plans = frozenset(
        row[0]
        for row in db.execute(
            "SELECT from_artifact FROM trace_edges WHERE edge_kind = 'forward_return'"
        ).fetchall()
        if row[0]
    )
    return DrivePassageInput(drive_plan_ids=drive_plans, forward_return_plan_ids=forward_return_plans)


def analyze_drive_passage(input_data: DrivePassageInput) -> DrivePassageResult:
    # 駆動 workflow は forward_return(戻し先)必須。drive_run に forward_return edge 不在 = violation。
    # 駆動 PLAN が 0 件なら検査対象なし = ok(absence-blindness でない: should-be 集合を正しく 0 と判定)。
    missing = tuple(
        plan_id for plan_id in input_data.drive_plan_ids if plan_id not in input_data.forward_return_plan_ids
    )
    return DrivePassageResult(ok=not missing, missing_forward_return=missing)


def drive_passage_messages(result: DrivePassageResult) -> list[Finding]:
    return [
        Finding(id=FN_DET_08, severity=HARD, subject=plan_id, missing=("forward_return absent",))
        for plan_id in result.missing_forward_return
    ]


FN_DET_05 = "FN-DET-05"


@dataclass(frozen=True)
class FnUtPairInput:
    l6_required_fns: tuple[str, ...]
    covered_fns: frozenset[str]


@dataclass(frozen=True)
class FnUtPairResult:
    ok: bool
    unpaired_fns: tuple[str, ...]


def load_fn_ut_pair_input(db: sqlite3.Connection) -> FnUtPairInput:
    _ensure_table_columns("functional_registry", ("fn_id", "layer"))
    _ensure_table_columns("test_cases", ("fr_id",))
    l6_required = tuple(
        row[0]
        for row in db.execute(
            "SELECT fn_id FROM functional_registry WHERE layer = 'L6_required' ORDER BY fn_id"
        ).fetchall()
        if row[0]
    )
    covered = frozenset(
        row[0]
        for row in db.execute("SELECT DISTINCT fr_id FROM test_cases WHERE fr_id != ''").fetchall()
        if row[0]
    )
    return FnUtPairInput(l6_required_fns=l6_required, covered_fns=covered)


def analyze_fn_ut_pair(input_data: FnUtPairInput) -> FnUtPairResult:
    # L6_required FR は covering UT(test が @covers で fr_id 宣言)必須。covered でない = unpaired。
    # L6_required が 0 件なら ok(should-be 集合を正しく空と判定)。waiver(FN-*/FR-* scheme 不一致)は follow-up。
    unpaired = tuple(fn for fn in input_data.l6_required_fns if fn not in input_data.covered_fns)
    return FnUtPairResult(ok=not unpaired, unpaired_fns=unpaired)


def fn_ut_pair_messages(result: FnUtPairResult) -> list[Finding]:
    return [
        Finding(id=FN_DET_05, severity=HARD, subject=fn, missing=("no covering UT (declare @covers in test)",))
        for fn in result.unpaired_fns
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
        detector_id=FN_DET_11,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_db_projection_coverage_input,
        analyze=analyze_db_projection_coverage,
        messages=db_projection_coverage_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_12,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_schema_ssot_input,
        analyze=analyze_schema_ssot,
        messages=schema_ssot_messages,
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
    DetectorSpec(
        detector_id=FN_DET_10,
        source_kind=FILE_SNAPSHOT,
        severity=HARD,
        load=load_lint_wiring_input,
        analyze=analyze_lint_wiring,
        messages=lint_wiring_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_14,
        source_kind=FILE_SNAPSHOT,
        severity=HARD,
        load=load_dist_api_input,
        analyze=analyze_dist_api,
        messages=dist_api_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_08,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_drive_passage_input,
        analyze=analyze_drive_passage,
        messages=drive_passage_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_05,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_fn_ut_pair_input,
        analyze=analyze_fn_ut_pair,
        messages=fn_ut_pair_messages,
    ),
)
