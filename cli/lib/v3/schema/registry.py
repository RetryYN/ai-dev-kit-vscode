from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .identifiers import SchemaError, assert_sql_identifier
from .tables_core import CORE_TABLE_SPECS
from .tables_evaluation import EVALUATION_TABLE_SPECS
from .tables_graph import GRAPH_TABLE_SPECS

SCHEMA_VERSION = 18
VALID_TABLE_KINDS = frozenset({"projection", "append_event", "config"})


@dataclass(frozen=True)
class ColumnDef:
    name: str
    sql_type: str
    primary_key: bool = False
    nullable: bool = False
    references: tuple[str, str] | None = None


@dataclass(frozen=True)
class TableDef:
    name: str
    kind: str
    columns: tuple[ColumnDef, ...]
    logical_keys: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class IndexDef:
    name: str
    table_name: str
    column_names: tuple[str, ...]
    unique: bool = False


def col(name: str, sql_type: str, *, nullable: bool = False, references: tuple[str, str] | None = None) -> ColumnDef:
    return ColumnDef(name=name, sql_type=sql_type, nullable=nullable, references=references)


def pk(name: str = "id", sql_type: str = "TEXT") -> ColumnDef:
    return ColumnDef(name=name, sql_type=sql_type, primary_key=True)


def _build_column(spec: tuple[str, str, str]) -> ColumnDef:
    kind, name, sql_type = spec
    if kind == "pk":
        return pk(name, sql_type)
    if kind == "col":
        return col(name, sql_type)
    raise SchemaError(f"unknown column spec kind: {kind!r}")


def _build_table(name: str, kind: str, column_specs: tuple[tuple[str, str, str], ...]) -> TableDef:
    logical_keys = (("ut_id", "run_id", "seq"),) if name == "test_result_events" else ()
    return TableDef(
        name=name,
        kind=kind,
        columns=tuple(_build_column(spec) for spec in column_specs),
        logical_keys=logical_keys,
    )


TABLES = tuple(
    _build_table(name, kind, column_specs)
    for name, kind, column_specs in (*CORE_TABLE_SPECS, *EVALUATION_TABLE_SPECS, *GRAPH_TABLE_SPECS)
)
INDEX_SPECS = (
    ("idx_plan_layer_drive_status", "plan_registry", ("plan_id", "layer", "drive", "status")),
    ("idx_trace_from_to", "trace_edges", ("from_artifact", "to_artifact")),
    ("idx_findings_subject_status", "findings", ("subject_id", "status", "severity")),
    ("idx_hook_session_plan", "hook_events", ("session_id", "plan_id", "occurred_at")),
    ("idx_skill_plan_skill", "skill_invocations", ("plan_id", "skill_id", "fired_at")),
    ("idx_issue_queue_plan_status", "issue_queue", ("plan_id", "status", "created_at")),
    ("idx_trouble_events_plan_category", "trouble_events", ("plan_id", "category", "created_at")),
    ("idx_retry_events_plan_phase", "retry_events", ("plan_id", "workflow", "phase")),
    ("idx_improvement_log_status", "improvement_log", ("status", "created_at")),
    ("idx_search_subject", "search_index", ("subject_type", "subject_id")),
    ("idx_graph_node_type_subject", "graph_nodes", ("node_type", "subject_id")),
    ("idx_graph_path", "graph_nodes", ("path",)),
    ("idx_dependency_from_kind", "dependency_edges", ("from_node_id", "edge_kind")),
    ("idx_dependency_to_kind", "dependency_edges", ("to_node_id", "edge_kind")),
    ("idx_impact_change_status", "impact_results", ("change_set_id", "status")),
    ("idx_artifact_progress_color", "artifact_progress", ("color", "state")),
    ("idx_artifact_progress_tests", "artifact_progress", ("passed_test_run_count", "dependency_checked")),
    ("idx_artifact_progress_events_path", "artifact_progress_events", ("artifact_path", "occurred_at")),
    ("idx_feedback_source", "feedback_events", ("source_table", "source_id")),
    ("idx_tool_name_scope", "tool_runs", ("tool_name", "input_scope")),
    ("idx_diagram_scope_format", "diagram_artifacts", ("scope", "format")),
    ("idx_mcp_profile_name", "mcp_server_profiles", ("name",)),
    ("idx_mcp_triggers_signal", "mcp_profile_triggers", ("signal", "workflow", "gate")),
    ("idx_mcp_runs_profile_plan", "mcp_server_runs", ("mcp_profile_id", "plan_id", "started_at")),
    ("idx_verification_profile_type", "verification_profiles", ("profile_type", "enabled")),
    ("idx_verification_recommendations_change", "verification_recommendations", ("change_set_id", "profile_kind", "accepted")),
    ("idx_external_tool_findings_subject", "external_tool_findings", ("subject_id", "status", "severity")),
    ("idx_document_export_run_family", "document_export_runs", ("source_doc_family", "plan_id")),
    ("idx_document_export_run_snapshot", "document_export_runs", ("source_snapshot_hash",)),
    ("idx_document_export_artifact_format", "document_export_artifacts", ("format", "stale_status")),
    ("idx_document_export_profile_family", "document_export_profiles", ("source_doc_family", "format", "enabled")),
    ("idx_document_export_triggers_signal", "document_export_triggers", ("signal", "workflow", "gate")),
    ("idx_roadmap_band_status", "roadmap_band_coverage", ("status", "band_id")),
    ("idx_roadmap_gate_plan", "roadmap_gate_progress", ("plan_id", "reached")),
    ("idx_review_evidence_plan", "review_evidence_registry", ("plan_id", "has_evidence")),
    ("idx_descent_obligation_trace_status", "descent_obligations", ("trace_key", "status", "required_layer")),
    ("idx_skill_evaluations_unused", "skill_evaluations", ("unused_flag", "skill_rating")),
    ("idx_poc_evaluations_rate", "poc_evaluations", ("poc_success_rate", "evaluated_at")),
    ("idx_model_evaluations_rate", "model_evaluations", ("success_rate", "evaluated_at")),
    ("idx_screens_category", "screens", ("category", "screen_id")),
    ("idx_screen_trace_screen", "screen_trace", ("screen_id", "requirement_kind")),
)
INDEXES = tuple(
    IndexDef(name=name, table_name=table_name, column_names=tuple(column_names))
    for name, table_name, column_names in INDEX_SPECS
)
TABLE_BY_NAME = {table.name: table for table in TABLES}


def validate_registry(
    tables: Iterable[TableDef] | None = None,
    indexes: Iterable[IndexDef] | None = None,
) -> None:
    table_list = tuple(TABLES if tables is None else tables)
    index_list = tuple(INDEXES if indexes is None else indexes)
    seen_tables: set[str] = set()

    for table in table_list:
        assert_sql_identifier(table.name)
        if table.name in seen_tables:
            raise SchemaError(f"duplicate table name: {table.name}")
        seen_tables.add(table.name)
        if table.kind not in VALID_TABLE_KINDS:
            raise SchemaError(f"invalid table kind: {table.kind!r}")
        if not table.columns:
            raise SchemaError(f"table must define at least one column: {table.name}")
        seen_columns: set[str] = set()
        for column in table.columns:
            assert_sql_identifier(column.name)
            if column.name in seen_columns:
                raise SchemaError(f"duplicate column name: {table.name}.{column.name}")
            seen_columns.add(column.name)
        for logical_key in table.logical_keys:
            if not logical_key:
                raise SchemaError(f"logical key must include at least one column: {table.name}")
            for column_name in logical_key:
                assert_sql_identifier(column_name)
                if column_name not in seen_columns:
                    raise SchemaError(f"logical key column not found: {table.name}.{column_name}")

    by_name = {table.name: table for table in table_list}
    for table in table_list:
        for column in table.columns:
            if column.references is None:
                continue
            target_table, target_column = column.references
            if "." in target_table:
                raise SchemaError(f"cross-db foreign keys are not allowed: {table.name}.{column.name} -> {target_table}")
            assert_sql_identifier(target_table)
            assert_sql_identifier(target_column)
            if target_table not in by_name:
                raise SchemaError(f"foreign key target not found: {target_table}")
            if target_column not in {item.name for item in by_name[target_table].columns}:
                raise SchemaError(f"foreign key column not found: {target_table}.{target_column}")

    seen_indexes: set[str] = set()
    for index in index_list:
        assert_sql_identifier(index.name)
        assert_sql_identifier(index.table_name)
        if index.name in seen_indexes:
            raise SchemaError(f"duplicate index name: {index.name}")
        seen_indexes.add(index.name)
        if index.table_name not in by_name:
            raise SchemaError(f"index target table not found: {index.table_name}")
        if not index.column_names:
            raise SchemaError(f"index must include at least one column: {index.name}")
        table_columns = {column.name for column in by_name[index.table_name].columns}
        for column_name in index.column_names:
            assert_sql_identifier(column_name)
            if column_name not in table_columns:
                raise SchemaError(f"index column not found: {index.table_name}.{column_name}")
