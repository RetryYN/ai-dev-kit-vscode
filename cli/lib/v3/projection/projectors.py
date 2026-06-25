from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from cli.lib.v3.schema import registry

from .secret_guard import SensitivePayloadError, assert_no_sensitive_payload
from .sources import SourceRecord
from .upsert import stable_id, upsert_row


@dataclass
class ProjectionContext:
    db: sqlite3.Connection
    sources: list[SourceRecord]
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fails: list[str] = field(default_factory=list)


def _record_count(ctx: ProjectionContext, table_name: str) -> None:
    ctx.counts[table_name] = ctx.counts.get(table_name, 0) + 1


def _record_finding(
    ctx: ProjectionContext,
    *,
    kind: str,
    severity: str,
    subject_id: str,
    source: str,
    status: str,
    evidence_path: str,
) -> None:
    upsert_row(
        ctx.db,
        registry.TABLE_BY_NAME["findings"],
        {
            "kind": kind,
            "severity": severity,
            "subject_id": subject_id,
            "source": source,
            "status": status,
            "evidence_path": evidence_path,
        },
    )
    _record_count(ctx, "findings")
    if status == "fail":
        ctx.fails.append(subject_id)
    else:
        ctx.warnings.append(subject_id)


def record_parse_failures(ctx: ProjectionContext) -> None:
    for source in ctx.sources:
        if source.parse_error is None:
            continue
        _record_finding(
            ctx,
            kind="invalid-frontmatter",
            severity="high",
            subject_id=source.path,
            source=source.parse_error,
            status="fail",
            evidence_path=source.path,
        )


def _source_kind(source: SourceRecord) -> str:
    value = source.frontmatter.get("source_kind")
    return value if isinstance(value, str) else ""


def _matching_sources(ctx: ProjectionContext, kind: str) -> list[SourceRecord]:
    return [source for source in ctx.sources if source.parse_error is None and _source_kind(source) == kind]


def _is_plan_source(source: SourceRecord) -> bool:
    if source.parse_error is not None:
        return False
    if _source_kind(source) == "plan":
        return True
    return all(source.frontmatter.get(field) for field in ("plan_id", "kind", "layer", "drive", "status"))


def _is_inferred_plan_source(source: SourceRecord) -> bool:
    return _is_plan_source(source) and not _source_kind(source)


def _is_inferred_design_doc(source: SourceRecord) -> bool:
    return source.parse_error is None and not _source_kind(source) and source.path.startswith("docs/v3/")


def _table_column_names(table_name: str) -> set[str]:
    return {column.name for column in registry.TABLE_BY_NAME[table_name].columns}


def _filter_row(table_name: str, row: dict[str, object]) -> dict[str, object]:
    columns = _table_column_names(table_name)
    return {key: value for key, value in row.items() if key in columns}


def _stringify(value: object, *, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _first_non_empty(*values: object) -> str:
    for value in values:
        candidate = _stringify(value).strip()
        if candidate:
            return candidate
    return ""


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _path_list(value: object, *, self_path: str | None = None) -> list[str]:
    paths: list[str] = []
    for item in _as_list(value):
        candidate = _stringify(item).strip()
        if not candidate:
            continue
        if candidate == "self" and self_path is not None:
            paths.append(self_path)
            continue
        paths.append(candidate)
    return paths


def _updated_at(source: SourceRecord) -> str:
    return _first_non_empty(
        source.frontmatter.get("updated_at"),
        source.frontmatter.get("revised"),
        source.frontmatter.get("created"),
    )


def _plan_parent(source: SourceRecord) -> str:
    dependencies = source.frontmatter.get("dependencies")
    dependency_parent = dependencies.get("parent") if isinstance(dependencies, dict) else None
    return _first_non_empty(source.frontmatter.get("parent"), dependency_parent, source.frontmatter.get("parent_process"))


def _safe_upsert_projection_row(
    ctx: ProjectionContext,
    *,
    table_name: str,
    source: SourceRecord,
    row: dict[str, object],
) -> bool:
    table = registry.TABLE_BY_NAME[table_name]
    try:
        assert_no_sensitive_payload(row, table)
    except SensitivePayloadError as exc:
        _record_finding(
            ctx,
            kind="secret-guard-blocked",
            severity="warning",
            subject_id=source.path,
            source=str(exc),
            status="warn",
            evidence_path=source.path,
        )
        return False
    upsert_row(ctx.db, table, row)
    _record_count(ctx, table.name)
    return True


def _require_fields(ctx: ProjectionContext, source: SourceRecord, fields: tuple[str, ...]) -> bool:
    missing = [field for field in fields if not source.frontmatter.get(field)]
    if not missing:
        return True
    _record_finding(
        ctx,
        kind="contract-violation",
        severity="warning",
        subject_id=source.path,
        source=", ".join(missing),
        status="warn",
        evidence_path=source.path,
    )
    return False


def project_plans(ctx: ProjectionContext) -> None:
    table = registry.TABLE_BY_NAME["plan_registry"]
    for source in ctx.sources:
        if not _is_plan_source(source):
            continue
        if not _require_fields(ctx, source, ("plan_id", "kind", "layer", "drive", "status")):
            continue
        updated_at = _updated_at(source)
        if not updated_at:
            _record_finding(
                ctx,
                kind="contract-violation",
                severity="warning",
                subject_id=source.path,
                source="updated_at",
                status="warn",
                evidence_path=source.path,
            )
            continue
        row = _filter_row(
            table.name,
            {
                "plan_id": _stringify(source.frontmatter.get("plan_id")),
                "kind": _stringify(source.frontmatter.get("kind")),
                "layer": _stringify(source.frontmatter.get("layer")),
                "sub_doc": _stringify(source.frontmatter.get("sub_doc")),
                "drive": _stringify(source.frontmatter.get("drive")),
                "status": _stringify(source.frontmatter.get("status")),
                "parent": _plan_parent(source),
                "updated_at": updated_at,
                "decision_outcome": _stringify(source.frontmatter.get("decision_outcome")),
                "source_hash": source.content_hash,
            },
        )
        _safe_upsert_projection_row(ctx, table_name=table.name, source=source, row=row)


def project_artifacts(ctx: ProjectionContext) -> None:
    artifact_table = registry.TABLE_BY_NAME["artifact_registry"]
    for source in _matching_sources(ctx, "artifact"):
        if not _require_fields(ctx, source, ("artifact_type", "path", "status")):
            continue
        row = _filter_row(
            artifact_table.name,
            {
                "artifact_type": _stringify(source.frontmatter.get("artifact_type")),
                "path": _stringify(source.frontmatter.get("path")),
                "pair_artifact": _stringify(source.frontmatter.get("pair_artifact")),
                "status": _stringify(source.frontmatter.get("status")),
                "updated_at": _updated_at(source),
            },
        )
        _safe_upsert_projection_row(ctx, table_name=artifact_table.name, source=source, row=row)

    for source in ctx.sources:
        if not (_is_inferred_plan_source(source) or _is_inferred_design_doc(source)):
            continue
        pair_candidates = _path_list(source.frontmatter.get("pairs_test_design"), self_path=source.path)
        pair_candidates.extend(_path_list(source.frontmatter.get("pair_artifact"), self_path=source.path))
        row = _filter_row(
            artifact_table.name,
            {
                "artifact_type": "plan" if _is_inferred_plan_source(source) else _first_non_empty(source.frontmatter.get("artifact_type"), "design_doc"),
                "path": source.path,
                "pair_artifact": pair_candidates[0] if pair_candidates else "",
                "status": _first_non_empty(source.frontmatter.get("status"), "draft"),
                "updated_at": _updated_at(source),
            },
        )
        _safe_upsert_projection_row(ctx, table_name=artifact_table.name, source=source, row=row)

    export_table = registry.TABLE_BY_NAME["document_export_artifacts"]
    grouped: dict[str, list[SourceRecord]] = defaultdict(list)
    for source in _matching_sources(ctx, "document_export"):
        if not _require_fields(
            ctx,
            source,
            ("export_run_id", "format", "path", "renderer", "byte_size", "created_at", "evidence_path"),
        ):
            continue
        grouped[source.frontmatter["path"]].append(source)

    for export_path, grouped_sources in grouped.items():
        by_created = sorted(grouped_sources, key=lambda item: (item.frontmatter["created_at"], item.content_hash))
        current_hash = by_created[-1].content_hash if by_created else ""
        for source in by_created:
            row = {
                "document_export_artifact_id": stable_id(
                    export_table.name,
                    f"{export_path}:{source.content_hash}",
                ),
                "export_run_id": source.frontmatter["export_run_id"],
                "format": source.frontmatter["format"],
                "path": export_path,
                "renderer": source.frontmatter["renderer"],
                "byte_size": int(source.frontmatter["byte_size"]),
                "hash": source.content_hash,
                "created_at": source.frontmatter["created_at"],
                "evidence_path": source.frontmatter["evidence_path"],
                "stale_status": "current" if source.content_hash == current_hash else "stale",
            }
            assert_no_sensitive_payload(row, export_table)
            upsert_row(ctx.db, export_table, row)
            _record_count(ctx, export_table.name)


def project_trace_edges(ctx: ProjectionContext) -> None:
    known_artifacts = {
        row[0]
        for row in ctx.db.execute("SELECT path FROM artifact_registry").fetchall()
    }
    known_plans = {
        row[0]
        for row in ctx.db.execute("SELECT plan_id FROM plan_registry").fetchall()
    }
    plan_paths = {
        _stringify(source.frontmatter.get("plan_id")): source.path
        for source in ctx.sources
        if _is_plan_source(source) and source.frontmatter.get("plan_id")
    }

    def record_edge(
        source: SourceRecord,
        *,
        from_artifact: str,
        to_artifact: str,
        edge_kind: str,
        plan_id: str,
        status: str,
    ) -> None:
        table = registry.TABLE_BY_NAME["trace_edges"]
        row = _filter_row(
            table.name,
            {
                "from_artifact": from_artifact,
                "to_artifact": to_artifact,
                "edge_kind": edge_kind,
                "plan_id": plan_id,
                "status": status,
            },
        )
        inserted = _safe_upsert_projection_row(ctx, table_name=table.name, source=source, row=row)
        if not inserted:
            return

        unresolved = [reference for reference in (from_artifact, to_artifact) if reference not in known_artifacts]
        if plan_id and plan_id not in known_plans:
            unresolved.append(plan_id)
        if unresolved:
            _record_finding(
                ctx,
                kind="unresolved-join",
                severity="warning",
                subject_id=source.path,
                source=",".join(unresolved),
                status="warn",
                evidence_path=source.path,
            )

    for source in _matching_sources(ctx, "trace_edge"):
        if not _require_fields(ctx, source, ("from_artifact", "to_artifact", "edge_kind", "plan_id", "status")):
            continue
        record_edge(
            source,
            from_artifact=_stringify(source.frontmatter.get("from_artifact")),
            to_artifact=_stringify(source.frontmatter.get("to_artifact")),
            edge_kind=_stringify(source.frontmatter.get("edge_kind")),
            plan_id=_stringify(source.frontmatter.get("plan_id")),
            status=_stringify(source.frontmatter.get("status")),
        )

    for source in ctx.sources:
        if not _is_plan_source(source):
            continue
        plan_id = _stringify(source.frontmatter.get("plan_id"))
        status = _first_non_empty(source.frontmatter.get("status"), "active")

        for pair_path in _path_list(source.frontmatter.get("pairs_test_design"), self_path=source.path):
            record_edge(
                source,
                from_artifact=source.path,
                to_artifact=pair_path,
                edge_kind="pairs_with",
                plan_id=plan_id,
                status=status,
            )
            if pair_path != source.path:
                record_edge(
                    source,
                    from_artifact=pair_path,
                    to_artifact=source.path,
                    edge_kind="pairs_with",
                    plan_id=plan_id,
                    status=status,
                )

        for generated in _as_list(source.frontmatter.get("generates")):
            if isinstance(generated, dict):
                artifact_path = _first_non_empty(generated.get("artifact_path"), generated.get("path"))
            else:
                artifact_path = _stringify(generated).strip()
            if not artifact_path:
                continue
            record_edge(
                source,
                from_artifact=source.path,
                to_artifact=artifact_path,
                edge_kind="generates",
                plan_id=plan_id,
                status=status,
            )
            record_edge(
                source,
                from_artifact=artifact_path,
                to_artifact=source.path,
                edge_kind="generated_by",
                plan_id=plan_id,
                status=status,
            )

        dependencies = source.frontmatter.get("dependencies")
        requires = dependencies.get("requires") if isinstance(dependencies, dict) else []
        for required in _as_list(requires):
            required_plan_id = _stringify(required).strip()
            if not required_plan_id:
                continue
            required_path = plan_paths.get(required_plan_id, required_plan_id)
            record_edge(
                source,
                from_artifact=source.path,
                to_artifact=required_path,
                edge_kind="requires",
                plan_id=plan_id,
                status=status,
            )
            record_edge(
                source,
                from_artifact=required_path,
                to_artifact=source.path,
                edge_kind="required_by",
                plan_id=plan_id,
                status=status,
            )

    for source in ctx.sources:
        if source.parse_error is not None or _source_kind(source) or not source.frontmatter.get("pair_artifact"):
            continue
        for pair_path in _path_list(source.frontmatter.get("pair_artifact"), self_path=source.path):
            plan_id = _stringify(source.frontmatter.get("plan_id"))
            status = _first_non_empty(source.frontmatter.get("status"), "active")
            record_edge(
                source,
                from_artifact=source.path,
                to_artifact=pair_path,
                edge_kind="pairs_with",
                plan_id=plan_id,
                status=status,
            )
            if pair_path != source.path:
                record_edge(
                    source,
                    from_artifact=pair_path,
                    to_artifact=source.path,
                    edge_kind="pairs_with",
                    plan_id=plan_id,
                    status=status,
                )


def project_test_evidence(ctx: ProjectionContext) -> None:
    run_table = registry.TABLE_BY_NAME["test_runs"]
    case_table = registry.TABLE_BY_NAME["test_cases"]
    result_table = registry.TABLE_BY_NAME["test_results"]
    for source in _matching_sources(ctx, "test_evidence"):
        if not _require_fields(
            ctx,
            source,
            ("run_id", "ut_id", "status", "command", "runner", "started_at", "completed_at"),
        ):
            continue
        run_row = {
            "test_run_id": source.frontmatter["run_id"],
            "session_id": source.frontmatter.get("session_id", ""),
            "plan_id": source.frontmatter.get("plan_id", ""),
            "command": source.frontmatter["command"],
            "runner": source.frontmatter["runner"],
            "runtime": source.frontmatter.get("runtime", "python"),
            "os": source.frontmatter.get("os", "linux"),
            "shell": source.frontmatter.get("shell", "bash"),
            "scope": source.frontmatter.get("scope", "unit"),
            "started_at": source.frontmatter["started_at"],
            "completed_at": source.frontmatter["completed_at"],
            "exit_code": int(source.frontmatter.get("exit_code", "0")),
            "evidence_path": source.path,
            "output_digest": source.content_hash,
            "green_definition_id": source.frontmatter.get("green_definition_id", ""),
            "status": source.frontmatter["status"],
        }
        case_row = {
            "test_case_id": source.frontmatter["ut_id"],
            "test_run_id": source.frontmatter["run_id"],
            "test_file": source.frontmatter.get("test_file", source.path),
            "test_name": source.frontmatter.get("test_name", source.frontmatter["ut_id"]),
            "plan_id": source.frontmatter.get("plan_id", ""),
            "fr_id": source.frontmatter.get("fr_id", ""),
            "artifact_id": source.frontmatter.get("artifact_id", ""),
            "kind": source.frontmatter.get("kind", "unit"),
            "oracle_id": source.frontmatter.get("oracle_id", ""),
            "name": source.frontmatter.get("name", source.frontmatter["ut_id"]),
            "first_seen_at": source.frontmatter["started_at"],
            "last_seen_at": source.frontmatter["completed_at"],
            "status": source.frontmatter["status"],
            "duration_ms": float(source.frontmatter.get("duration_ms", "0")),
            "evidence_path": source.path,
        }
        result_row = {
            "test_case_id": source.frontmatter["ut_id"],
            "test_run_id": source.frontmatter["run_id"],
            "oracle_id": source.frontmatter.get("oracle_id", ""),
            "status": source.frontmatter["status"],
            "duration_ms": float(source.frontmatter.get("duration_ms", "0")),
            "failure_digest": source.frontmatter.get("failure_digest", ""),
            "started_at": source.frontmatter["started_at"],
            "completed_at": source.frontmatter["completed_at"],
            "message": source.body,
            "evidence_path": source.path,
        }
        assert_no_sensitive_payload(run_row, run_table)
        assert_no_sensitive_payload(case_row, case_table)
        assert_no_sensitive_payload(result_row, result_table)
        upsert_row(ctx.db, run_table, run_row)
        upsert_row(ctx.db, case_table, case_row)
        upsert_row(ctx.db, result_table, result_row)
        _record_count(ctx, run_table.name)
        _record_count(ctx, case_table.name)
        _record_count(ctx, result_table.name)


def project_gate_runs(ctx: ProjectionContext) -> None:
    table = registry.TABLE_BY_NAME["gate_runs"]
    known_plans = {
        row[0]
        for row in ctx.db.execute("SELECT plan_id FROM plan_registry").fetchall()
    }
    for source in _matching_sources(ctx, "gate_run"):
        if not _require_fields(ctx, source, ("gate_id", "plan_id", "status", "checked_at", "evidence_path")):
            continue
        row = {
            "gate_run_id": stable_id(
                table.name,
                f"{source.frontmatter['gate_id']}:{source.frontmatter['plan_id']}:{source.frontmatter['checked_at']}",
            ),
            "gate_id": source.frontmatter["gate_id"],
            "plan_id": source.frontmatter["plan_id"],
            "status": source.frontmatter["status"],
            "checked_at": source.frontmatter["checked_at"],
            "evidence_path": source.frontmatter["evidence_path"],
        }
        assert_no_sensitive_payload(row, table)
        upsert_row(ctx.db, table, row)
        _record_count(ctx, table.name)
        if source.frontmatter["plan_id"] not in known_plans:
            _record_finding(
                ctx,
                kind="unresolved-join",
                severity="warning",
                subject_id=source.path,
                source=source.frontmatter["plan_id"],
                status="warn",
                evidence_path=source.path,
            )


def project_code(ctx: ProjectionContext) -> None:
    """Phase 7.2: code/test ファイル(.py/.bats)を artifact_registry へ。本文は保存せず path のみ(C-5)。"""
    artifact_table = registry.TABLE_BY_NAME["artifact_registry"]
    for source in ctx.sources:
        if source.parse_error is not None:
            continue
        if source.path.endswith(".py"):
            artifact_type = "python_module"
        elif source.path.endswith(".bats"):
            artifact_type = "script"
        else:
            continue
        row = _filter_row(
            artifact_table.name,
            {
                "artifact_type": artifact_type,
                "path": source.path,
                "pair_artifact": "",
                "status": "active",
                "updated_at": _updated_at(source),
            },
        )
        _safe_upsert_projection_row(ctx, table_name=artifact_table.name, source=source, row=row)


def project_test_files(ctx: ProjectionContext) -> None:
    """Phase 7.3: 実 .py/.bats test ファイルを test_cases へ(test_file/test_name/status=discovered、本文非保存=C-5)。"""
    import ast as _ast
    import re as _re

    case_table = registry.TABLE_BY_NAME["test_cases"]
    for source in ctx.sources:
        if source.parse_error is not None:
            continue
        path = source.path
        base = path.rsplit("/", 1)[-1]
        names: list[str] = []
        if path.endswith(".py") and (base.startswith("test_") or base.endswith("_test.py")):
            try:
                tree = _ast.parse(source.text)
            except SyntaxError:
                continue
            names = [
                node.name
                for node in _ast.walk(tree)
                if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef))
                and node.name.startswith("test")
            ]
            kind = "unit"
        elif path.endswith(".bats"):
            names = _re.findall(r"@test\s+['\"](.+?)['\"]", source.text)
            kind = "bats"
        else:
            continue
        for test_name in names:
            row = _filter_row(
                case_table.name,
                {
                    "test_case_id": stable_id(case_table.name, f"{path}::{test_name}"),
                    "test_run_id": "",
                    "test_file": path,
                    "test_name": test_name,
                    "plan_id": "",
                    "fr_id": "",
                    "artifact_id": "",
                    "kind": kind,
                    "oracle_id": "",
                    "name": test_name,
                    "first_seen_at": "",
                    "last_seen_at": "",
                    "status": "discovered",
                    "duration_ms": 0.0,
                    "evidence_path": path,
                },
            )
            _safe_upsert_projection_row(ctx, table_name=case_table.name, source=source, row=row)


PROJECTORS = (
    project_plans,
    project_artifacts,
    project_code,
    project_trace_edges,
    project_test_evidence,
    project_test_files,
    project_gate_runs,
)
