from __future__ import annotations

import ast
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

try:
    from v3.schema import registry
    from v3.projection.sources import _parse_frontmatter
except ImportError:  # pragma: no cover - repo-local fallback until top-level v3 package is wired.
    from cli.lib.v3.schema import registry
    from cli.lib.v3.projection.sources import _parse_frontmatter

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


FN_DET_04 = "FN-DET-04"


@dataclass(frozen=True)
class RequirementDescentInput:
    fr_ids: tuple[str, ...]
    design_reachable_fr_ids: frozenset[str]
    tested_fr_ids: frozenset[str]


@dataclass(frozen=True)
class RequirementDescentResult:
    ok: bool
    missing_design_fr_ids: tuple[str, ...]
    missing_test_fr_ids: tuple[str, ...]


def load_requirement_descent_input(db: sqlite3.Connection) -> RequirementDescentInput:
    _ensure_table_columns("functional_registry", ("fn_id",))
    _ensure_table_columns("artifact_registry", ("path", "artifact_type"))
    _ensure_table_columns("trace_edges", ("from_artifact", "to_artifact"))
    _ensure_table_columns("test_cases", ("fr_id",))

    fr_ids = tuple(
        row[0]
        for row in db.execute(
            "SELECT fn_id FROM functional_registry WHERE fn_id LIKE 'FR-%' ORDER BY fn_id"
        ).fetchall()
        if row[0]
    )
    design_reachable_fr_ids = frozenset(
        row[0]
        for row in db.execute(
            "SELECT DISTINCT e.from_artifact "
            "FROM trace_edges AS e "
            "JOIN artifact_registry AS a ON a.path = e.to_artifact "
            "WHERE e.from_artifact LIKE 'FR-%' "
            "AND a.artifact_type NOT IN ('python_module', 'script')"
        ).fetchall()
        if row[0]
    )
    tested_fr_ids = frozenset(
        row[0]
        for row in db.execute(
            "SELECT DISTINCT fr_id FROM test_cases WHERE fr_id LIKE 'FR-%' ORDER BY fr_id"
        ).fetchall()
        if row[0]
    )
    return RequirementDescentInput(
        fr_ids=fr_ids,
        design_reachable_fr_ids=design_reachable_fr_ids,
        tested_fr_ids=tested_fr_ids,
    )


def analyze_requirement_descent(input_data: RequirementDescentInput) -> RequirementDescentResult:
    # FR should-be 集合が空なら not-applicable として ok=true。source unreadable は loader 例外で fail-close。
    missing_design = tuple(
        fr_id for fr_id in input_data.fr_ids if fr_id not in input_data.design_reachable_fr_ids
    )
    missing_test = tuple(
        fr_id
        for fr_id in input_data.fr_ids
        if fr_id in input_data.design_reachable_fr_ids and fr_id not in input_data.tested_fr_ids
    )
    return RequirementDescentResult(
        ok=not missing_design and not missing_test,
        missing_design_fr_ids=missing_design,
        missing_test_fr_ids=missing_test,
    )


def requirement_descent_messages(result: RequirementDescentResult) -> list[Finding]:
    findings = [
        Finding(
            id=FN_DET_04,
            severity=HARD,
            subject=fr_id,
            missing=("no reachable design artifact via trace_edges",),
        )
        for fr_id in result.missing_design_fr_ids
    ]
    findings.extend(
        Finding(
            id=FN_DET_04,
            severity=HARD,
            subject=fr_id,
            missing=("design reachable but no downstream test_cases",),
        )
        for fr_id in result.missing_test_fr_ids
    )
    return findings


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
PLAN_ID_PATTERN = re.compile(r"^PLAN-(?:L[1-7]|DISCOVERY|REVERSE|RECOVERY|M)-\d{2}-[a-z0-9][a-z0-9-]*$")
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


FN_DET_17 = "FN-DET-17"
_ASSIGNMENT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.+)$")
_SOURCE_RE = re.compile(r"^(?:source|\.)\s+(.+?)(?:\s+#.*)?$")


@dataclass(frozen=True)
class ImportCycleInput:
    scanned: bool
    python_files: tuple[str, ...]
    bash_files: tuple[str, ...]
    adjacency: tuple[tuple[str, tuple[str, ...]], ...]
    missing_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportCycleResult:
    ok: bool
    missing_sources: tuple[str, ...]
    cycles: tuple[tuple[str, ...], ...]


def _normalize_repo_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _python_files(lib_root: Path) -> list[Path]:
    files: list[Path] = []
    if not lib_root.is_dir():
        return files
    for path in lib_root.rglob("*.py"):
        relative = path.relative_to(lib_root)
        if any(part in {"tests", "__pycache__"} for part in relative.parts):
            continue
        files.append(path.resolve())
    return sorted(files)


def _python_alias_map(lib_root: Path, paths: list[Path]) -> tuple[dict[str, Path], dict[Path, str]]:
    alias_map: dict[str, Path] = {}
    package_map: dict[Path, str] = {}
    for path in paths:
        relative = path.relative_to(lib_root)
        parts = list(relative.parts)
        parent_parts = parts[:-1]
        package_suffix = ".".join(parent_parts)
        package_map[path] = "cli.lib" + (f".{package_suffix}" if package_suffix else "")

        module_parts = parent_parts if path.stem == "__init__" else [*parent_parts, path.stem]
        if not module_parts:
            continue
        dotted = ".".join(module_parts)
        for alias in {dotted, f"cli.lib.{dotted}"}:
            alias_map[alias] = path
    return alias_map, package_map


def _resolve_python_targets(
    node: ast.ImportFrom,
    *,
    current_package: str,
    alias_map: dict[str, Path],
) -> set[Path]:
    if node.level > 0:
        package_parts = current_package.split(".")
        strip_count = max(0, node.level - 1)
        if strip_count >= len(package_parts):
            return set()
        base = ".".join(package_parts[: len(package_parts) - strip_count])
        resolved_module = f"{base}.{node.module}" if node.module else base
    else:
        resolved_module = node.module or ""

    targets: set[Path] = set()
    if not node.module:
        for alias in node.names:
            candidate = f"{resolved_module}.{alias.name}" if resolved_module else alias.name
            target = alias_map.get(candidate)
            if target is not None:
                targets.add(target)
        return targets

    submodule_targets: list[Path] = []
    for alias in node.names:
        candidate = f"{resolved_module}.{alias.name}" if resolved_module else alias.name
        target = alias_map.get(candidate)
        if target is not None:
            submodule_targets.append(target)
    if submodule_targets:
        targets.update(submodule_targets)
        return targets

    base_target = alias_map.get(resolved_module)
    if base_target is not None:
        targets.add(base_target)
    return targets


def _python_adjacency(repo_root: Path) -> tuple[tuple[str, ...], dict[str, set[str]]]:
    lib_root = repo_root / "cli" / "lib"
    paths = _python_files(lib_root)
    alias_map, package_map = _python_alias_map(lib_root, paths)
    adjacency = {_normalize_repo_path(path, repo_root): set() for path in paths}

    for path in paths:
        node_key = _normalize_repo_path(path, repo_root)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            targets: set[Path] = set()
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias_map.get(alias.name)
                    if target is not None:
                        targets.add(target)
            elif isinstance(node, ast.ImportFrom):
                targets = _resolve_python_targets(
                    node,
                    current_package=package_map[path],
                    alias_map=alias_map,
                )
            if not targets:
                continue
            for target in targets:
                target_key = _normalize_repo_path(target, repo_root)
                if target_key != node_key:
                    adjacency[node_key].add(target_key)
    return tuple(sorted(adjacency)), adjacency


def _is_shell_script(path: Path) -> bool:
    if path.suffix == ".sh":
        return True
    try:
        first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    except (IndexError, OSError):
        return False
    return first_line.startswith("#!") and ("bash" in first_line or first_line.endswith("/sh"))


def _bash_files(cli_root: Path) -> list[Path]:
    files: list[Path] = []
    if not cli_root.is_dir():
        return files
    for path in cli_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(cli_root)
        if any(part in {"tests", "__pycache__"} for part in relative.parts):
            continue
        if path.parent == cli_root / "lib":
            continue
        if _is_shell_script(path):
            files.append(path.resolve())
    return sorted(files)


def _substitute_bash_vars(value: str, variables: dict[str, str]) -> str:
    resolved = value
    for key, replacement in variables.items():
        resolved = resolved.replace(f"${{{key}}}", replacement)
        resolved = resolved.replace(f"${key}", replacement)
    return resolved


def _resolve_bash_expression(expr: str, *, path: Path, variables: dict[str, str]) -> Path | None:
    value = expr.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    script_dir = path.parent.resolve()
    replacements = {
        '$(cd "$(dirname "$0")" && pwd)': script_dir.as_posix(),
        '$(cd "$(dirname "$0")/.." && pwd)': script_dir.parent.resolve().as_posix(),
        '$(dirname "$0")': script_dir.as_posix(),
    }
    for needle, replacement in replacements.items():
        value = value.replace(needle, replacement)
    value = _substitute_bash_vars(value, variables)
    if "$(" in value or re.search(r"\$[{A-Za-z_]", value):
        return None
    if "/" not in value and not value.startswith("."):
        return None

    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (script_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        return candidate if candidate.is_file() else None
    except OSError:
        return None


def _bash_adjacency(repo_root: Path) -> tuple[tuple[str, ...], dict[str, set[str]]]:
    cli_root = repo_root / "cli"
    paths = _bash_files(cli_root)
    known = {path.resolve() for path in paths}
    adjacency = {_normalize_repo_path(path, repo_root): set() for path in paths}

    for path in paths:
        variables = {"SCRIPT_DIR": path.parent.resolve().as_posix()}
        node_key = _normalize_repo_path(path, repo_root)
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            assignment_match = _ASSIGNMENT_RE.match(line)
            if assignment_match and not line.startswith(("source ", ". ")):
                resolved_value = _resolve_bash_expression(
                    assignment_match.group(2),
                    path=path,
                    variables=variables,
                )
                if resolved_value is not None:
                    variables[assignment_match.group(1)] = resolved_value.as_posix()
                    continue
                value = assignment_match.group(2).strip().strip('"').strip("'")
                variables[assignment_match.group(1)] = _substitute_bash_vars(value, variables)
                continue

            source_match = _SOURCE_RE.match(line)
            if not source_match:
                continue
            resolved_path = _resolve_bash_expression(
                source_match.group(1),
                path=path,
                variables=variables,
            )
            if resolved_path is None or resolved_path not in known:
                continue
            target_key = _normalize_repo_path(resolved_path, repo_root)
            if target_key != node_key:
                adjacency[node_key].add(target_key)
    return tuple(sorted(adjacency)), adjacency


def load_import_cycle_input(db: sqlite3.Connection) -> ImportCycleInput:
    del db
    repo_root = Path(_REPO_ROOT)
    if not repo_root.is_dir():
        return ImportCycleInput(scanned=False, python_files=(), bash_files=(), adjacency=(), missing_sources=("repo-root-unreadable",))

    try:
        python_files, python_adjacency = _python_adjacency(repo_root)
        bash_files, bash_adjacency = _bash_adjacency(repo_root)
    except OSError:
        return ImportCycleInput(scanned=False, python_files=(), bash_files=(), adjacency=(), missing_sources=("repo-root-unreadable",))

    merged: dict[str, tuple[str, ...]] = {}
    for node, dependencies in {**python_adjacency, **bash_adjacency}.items():
        merged[node] = tuple(sorted(dependencies))
    adjacency = tuple((node, merged[node]) for node in sorted(merged))
    return ImportCycleInput(
        scanned=True,
        python_files=python_files,
        bash_files=bash_files,
        adjacency=adjacency,
    )


def _canonicalize_cycle(cycle: list[str]) -> tuple[str, ...]:
    nodes = list(cycle)
    if len(nodes) > 1 and nodes[0] == nodes[-1]:
        nodes = nodes[:-1]
    if not nodes:
        return ()

    candidates: list[tuple[str, ...]] = []
    for variant in (nodes, list(reversed(nodes))):
        for index in range(len(variant)):
            rotated = tuple(variant[index:] + variant[:index])
            candidates.append(rotated)
    best = min(candidates)
    return (*best, best[0])


def _find_cycles(adjacency: dict[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    discovered: dict[tuple[str, ...], tuple[str, ...]] = {}
    visited: set[str] = set()
    stack: list[str] = []
    stack_lookup: set[str] = set()

    def dfs(node: str) -> None:
        visited.add(node)
        stack.append(node)
        stack_lookup.add(node)
        for dependency in adjacency.get(node, ()):
            if dependency in stack_lookup:
                start_index = stack.index(dependency)
                cycle = _canonicalize_cycle(stack[start_index:] + [dependency])
                discovered[cycle] = cycle
                continue
            if dependency not in visited:
                dfs(dependency)
        stack_lookup.remove(node)
        stack.pop()

    for node in sorted(adjacency):
        if node not in visited:
            dfs(node)
    return tuple(sorted(discovered))


def analyze_import_cycle(input_data: ImportCycleInput) -> ImportCycleResult:
    if not input_data.scanned:
        return ImportCycleResult(
            ok=False,
            missing_sources=input_data.missing_sources or ("repo-root-unreadable",),
            cycles=(),
        )

    if not input_data.python_files and not input_data.bash_files:
        return ImportCycleResult(ok=True, missing_sources=(), cycles=())

    adjacency = {node: dependencies for node, dependencies in input_data.adjacency}
    cycles = _find_cycles(adjacency)
    return ImportCycleResult(
        ok=not cycles,
        missing_sources=(),
        cycles=cycles,
    )


def import_cycle_messages(result: ImportCycleResult) -> list[Finding]:
    if result.missing_sources:
        return [Finding(id=FN_DET_17, severity=HARD, subject="import-cycle", missing=result.missing_sources)]
    return [
        Finding(
            id=FN_DET_17,
            severity=HARD,
            subject=" -> ".join(cycle),
            missing=(),
        )
        for cycle in result.cycles
    ]


FN_DET_15 = "FN-DET-15"
PLAN_SECTION_MARKERS = tuple(f"§{index}" for index in range(8))


@dataclass(frozen=True)
class DocContractArtifact:
    path: str
    artifact_type: str
    frontmatter: dict[str, object]
    text: str
    error: str | None = None


@dataclass(frozen=True)
class DocContractInput:
    artifacts: tuple[DocContractArtifact, ...]


@dataclass(frozen=True)
class DocContractViolation:
    subject: str
    missing: tuple[str, ...]


@dataclass(frozen=True)
class DocContractResult:
    ok: bool
    violations: tuple[DocContractViolation, ...]


def _doc_kind(path: str, artifact_type: str) -> str:
    if artifact_type == "plan" or path.startswith("docs/plans/"):
        return "plan"
    return "design_doc"


def _resolve_artifact_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(_REPO_ROOT, path)


def load_doc_contract_input(db: sqlite3.Connection) -> DocContractInput:
    _ensure_table_columns("artifact_registry", ("path", "artifact_type"))
    artifacts: list[DocContractArtifact] = []
    rows = db.execute("SELECT path, artifact_type FROM artifact_registry WHERE path LIKE '%.md' ORDER BY path").fetchall()
    for path, artifact_type in rows:
        if not path:
            continue
        resolved = _resolve_artifact_path(path)
        try:
            with open(resolved, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            artifacts.append(DocContractArtifact(path=path, artifact_type=artifact_type or "", frontmatter={}, text="", error=str(exc)))
            continue
        try:
            frontmatter, _body = _parse_frontmatter(text)
            artifacts.append(DocContractArtifact(path=path, artifact_type=artifact_type or "", frontmatter=frontmatter, text=text))
        except ValueError as exc:
            artifacts.append(DocContractArtifact(path=path, artifact_type=artifact_type or "", frontmatter={}, text=text, error=f"frontmatter parse error: {exc}"))
    return DocContractInput(artifacts=tuple(artifacts))


def _missing_frontmatter(frontmatter: dict[str, object], required: tuple[str, ...]) -> tuple[str, ...]:
    missing: list[str] = []
    for key in required:
        if key not in frontmatter:
            missing.append(f"frontmatter missing: {key}")
            continue
        value = frontmatter[key]
        if value is None:
            missing.append(f"frontmatter missing: {key}")
        elif isinstance(value, str) and not value.strip():
            missing.append(f"frontmatter missing: {key}")
    return tuple(missing)


def _missing_plan_sections(text: str) -> tuple[str, ...]:
    missing: list[str] = []
    for marker in PLAN_SECTION_MARKERS:
        if not re.search(rf"(?m)^\s*#{{1,6}}\s+{re.escape(marker)}(?:\b|\s)", text):
            missing.append(f"missing section: {marker}")
    return tuple(missing)


def analyze_doc_contract(input_data: DocContractInput) -> DocContractResult:
    if not input_data.artifacts:
        return DocContractResult(ok=True, violations=())

    violations: list[DocContractViolation] = []
    for artifact in input_data.artifacts:
        if artifact.error is not None:
            violations.append(DocContractViolation(subject=artifact.path, missing=(artifact.error,)))
            continue
        if _doc_kind(artifact.path, artifact.artifact_type) == "plan":
            missing = _missing_frontmatter(
                artifact.frontmatter,
                ("plan_id", "kind", "layer", "drive", "status", "agent_slots", "generates", "dependencies", "review_evidence"),
            )
            if missing:
                violations.append(DocContractViolation(subject=artifact.path, missing=missing))
            plan_id = artifact.frontmatter.get("plan_id")
            if isinstance(plan_id, str) and plan_id and not PLAN_ID_PATTERN.match(plan_id):
                violations.append(DocContractViolation(subject=artifact.path, missing=(f"invalid plan_id: {plan_id}",)))
            missing_sections = _missing_plan_sections(artifact.text)
            if missing_sections:
                violations.append(DocContractViolation(subject=artifact.path, missing=missing_sections))
            continue
        missing = _missing_frontmatter(
            artifact.frontmatter,
            ("layer", "status", "pair_artifact", "sub_doc", "next_pair_freeze", "plan"),
        )
        if missing:
            violations.append(DocContractViolation(subject=artifact.path, missing=missing))
    return DocContractResult(ok=not violations, violations=tuple(violations))


def doc_contract_messages(result: DocContractResult) -> list[Finding]:
    return [Finding(id=FN_DET_15, severity=HARD, subject=violation.subject, missing=violation.missing) for violation in result.violations]


FN_DET_08 = "FN-DET-08"
FN_DET_18 = "FN-DET-18"


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


@dataclass(frozen=True)
class PlanDependencyEdge:
    from_artifact: str
    to_artifact: str


@dataclass(frozen=True)
class PlanDependencyInput:
    requires_edges: tuple[PlanDependencyEdge, ...]
    existing_plan_ids: frozenset[str]


@dataclass(frozen=True)
class PlanDependencyViolation:
    from_artifact: str
    to_artifact: str


@dataclass(frozen=True)
class PlanDependencyResult:
    ok: bool
    missing_sources: tuple[str, ...]
    violations: tuple[PlanDependencyViolation, ...]


def load_plan_dependency_input(db: sqlite3.Connection) -> PlanDependencyInput:
    _ensure_table_columns("trace_edges", ("from_artifact", "to_artifact", "edge_kind"))
    _ensure_table_columns("plan_registry", ("plan_id",))
    requires_edges = tuple(
        PlanDependencyEdge(from_artifact=row[0], to_artifact=row[1])
        for row in db.execute(
            "SELECT from_artifact, to_artifact "
            "FROM trace_edges WHERE edge_kind = 'requires' "
            "ORDER BY from_artifact, to_artifact"
        ).fetchall()
        if row[0] and row[1]
    )
    existing_plan_ids = frozenset(
        row[0] for row in db.execute("SELECT plan_id FROM plan_registry").fetchall() if row[0]
    )
    return PlanDependencyInput(
        requires_edges=requires_edges,
        existing_plan_ids=existing_plan_ids,
    )


def analyze_plan_dependency(input_data: PlanDependencyInput) -> PlanDependencyResult:
    # requires edge が 0 件なら検査対象なし = ok。source unreadable は loader 例外で fail-close。
    violations = tuple(
        PlanDependencyViolation(from_artifact=edge.from_artifact, to_artifact=edge.to_artifact)
        for edge in input_data.requires_edges
        if edge.to_artifact not in input_data.existing_plan_ids
    )
    return PlanDependencyResult(
        ok=not violations,
        missing_sources=(),
        violations=violations,
    )


def plan_dependency_messages(result: PlanDependencyResult) -> list[Finding]:
    if result.missing_sources:
        return [_absence_finding(FN_DET_18, "plan-dependency", result.missing_sources)]
    return [
        Finding(
            id=FN_DET_18,
            severity=HARD,
            subject=f"{violation.from_artifact} requires {violation.to_artifact}",
            missing=(f"missing plan_registry.plan_id: {violation.to_artifact}",),
        )
        for violation in result.violations
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
        detector_id=FN_DET_04,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_requirement_descent_input,
        analyze=analyze_requirement_descent,
        messages=requirement_descent_messages,
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
        detector_id=FN_DET_17,
        source_kind=FILE_SNAPSHOT,
        severity=HARD,
        load=load_import_cycle_input,
        analyze=analyze_import_cycle,
        messages=import_cycle_messages,
    ),
    DetectorSpec(
        detector_id=FN_DET_15,
        source_kind=FILE_SNAPSHOT,
        severity=HARD,
        load=load_doc_contract_input,
        analyze=analyze_doc_contract,
        messages=doc_contract_messages,
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
        detector_id=FN_DET_18,
        source_kind=DB_PROJECTION,
        severity=HARD,
        load=load_plan_dependency_input,
        analyze=analyze_plan_dependency,
        messages=plan_dependency_messages,
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
