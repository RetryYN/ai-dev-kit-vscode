from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field

from cli.lib.v3.schema import registry

from .secret_guard import assert_no_sensitive_payload
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


def _matching_sources(ctx: ProjectionContext, kind: str) -> list[SourceRecord]:
    return [
        source
        for source in ctx.sources
        if source.parse_error is None and source.frontmatter.get("source_kind") == kind
    ]


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
    for source in _matching_sources(ctx, "plan"):
        if not _require_fields(ctx, source, ("plan_id", "kind", "layer", "drive", "status", "updated_at")):
            continue
        row = {
            "plan_id": source.frontmatter["plan_id"],
            "kind": source.frontmatter["kind"],
            "layer": source.frontmatter["layer"],
            "sub_doc": source.frontmatter.get("sub_doc", ""),
            "drive": source.frontmatter["drive"],
            "status": source.frontmatter["status"],
            "parent": source.frontmatter.get("parent", ""),
            "updated_at": source.frontmatter["updated_at"],
            "decision_outcome": source.frontmatter.get("decision_outcome", ""),
            "source_hash": source.content_hash,
        }
        assert_no_sensitive_payload(row, table)
        upsert_row(ctx.db, table, row)
        _record_count(ctx, table.name)


def project_artifacts(ctx: ProjectionContext) -> None:
    artifact_table = registry.TABLE_BY_NAME["artifact_registry"]
    for source in _matching_sources(ctx, "artifact"):
        if not _require_fields(ctx, source, ("artifact_type", "path", "status", "updated_at")):
            continue
        row = {
            "artifact_type": source.frontmatter["artifact_type"],
            "path": source.frontmatter["path"],
            "pair_artifact": source.frontmatter.get("pair_artifact", ""),
            "status": source.frontmatter["status"],
            "updated_at": source.frontmatter["updated_at"],
        }
        assert_no_sensitive_payload(row, artifact_table)
        upsert_row(ctx.db, artifact_table, row)
        _record_count(ctx, artifact_table.name)

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
    table = registry.TABLE_BY_NAME["trace_edges"]
    known_artifacts = {
        row[0]
        for row in ctx.db.execute("SELECT path FROM artifact_registry").fetchall()
    }
    known_plans = {
        row[0]
        for row in ctx.db.execute("SELECT plan_id FROM plan_registry").fetchall()
    }
    for source in _matching_sources(ctx, "trace_edge"):
        if not _require_fields(ctx, source, ("from_artifact", "to_artifact", "edge_kind", "plan_id", "status")):
            continue
        unresolved = [
            reference
            for reference in (
                source.frontmatter["from_artifact"],
                source.frontmatter["to_artifact"],
            )
            if reference not in known_artifacts
        ]
        if source.frontmatter["plan_id"] not in known_plans:
            unresolved.append(source.frontmatter["plan_id"])
        row = {
            "from_artifact": source.frontmatter["from_artifact"],
            "to_artifact": source.frontmatter["to_artifact"],
            "edge_kind": source.frontmatter["edge_kind"],
            "plan_id": source.frontmatter["plan_id"],
            "status": source.frontmatter["status"],
        }
        assert_no_sensitive_payload(row, table)
        upsert_row(ctx.db, table, row)
        _record_count(ctx, table.name)
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


PROJECTORS = (
    project_plans,
    project_artifacts,
    project_trace_edges,
    project_test_evidence,
    project_gate_runs,
)
