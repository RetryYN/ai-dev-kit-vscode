from __future__ import annotations

ColumnSpec = tuple[str, str, str]
TableSpec = tuple[str, str, tuple[ColumnSpec, ...]]


def col(name: str, sql_type: str = "TEXT") -> ColumnSpec:
    return ("col", name, sql_type)


def pk(name: str, sql_type: str = "TEXT") -> ColumnSpec:
    return ("pk", name, sql_type)


EVALUATION_TABLE_SPECS = (
    ("skill_evaluations", "projection", (
        pk("skill_id"),
        col("skill_rating", "REAL"),
        col("adoption_count", "INTEGER"),
        col("success_count", "INTEGER"),
        col("unused_flag", "INTEGER"),
        col("evaluated_at"),
    )),
    ("poc_evaluations", "projection", (
        pk("poc_evaluation_id"),
        col("poc_success_rate", "REAL"),
        col("confirmed_count", "INTEGER"),
        col("rejected_count", "INTEGER"),
        col("pivot_count", "INTEGER"),
        col("total_count", "INTEGER"),
        col("evaluated_at"),
    )),
    ("model_evaluations", "projection", (
        pk("model"),
        col("success_rate", "REAL"),
        col("run_count", "INTEGER"),
        col("success_count", "INTEGER"),
        col("evaluated_at"),
        col("total_input_tokens", "INTEGER"),
        col("total_output_tokens", "INTEGER"),
        col("total_cost_usd", "REAL"),
        col("tokens_per_success", "REAL"),
        col("cost_per_success", "REAL"),
    )),
    ("roadmap_rollups", "projection", (
        pk("rollup_id"),
        col("total_bands", "INTEGER"),
        col("covered_bands", "INTEGER"),
        col("parked_bands", "INTEGER"),
        col("uncovered_bands", "INTEGER"),
        col("total_gates", "INTEGER"),
        col("reached_gates", "INTEGER"),
        col("total_spans", "INTEGER"),
        col("confirmed_spans", "INTEGER"),
        col("frontier"),
        col("computed_at"),
    )),
    ("roadmap_band_coverage", "projection", (
        pk("band_id"),
        col("name"),
        col("status"),
        col("roadmap_ids"),
        col("computed_at"),
    )),
    ("roadmap_gate_progress", "projection", (
        pk("roadmap_gate_id"),
        col("plan_id"),
        col("gate_id"),
        col("total_spans", "INTEGER"),
        col("confirmed_spans", "INTEGER"),
        col("reached", "INTEGER"),
        col("computed_at"),
    )),
    ("review_evidence_registry", "projection", (
        pk("review_evidence_id"),
        col("plan_id"),
        col("kind"),
        col("status"),
        col("has_evidence", "INTEGER"),
        col("review_kind"),
        col("verdict"),
        col("reviewed_at"),
        col("tests_green_at"),
        col("worker_model"),
        col("reviewer_model"),
        col("source"),
        col("indexed_at"),
    )),
    ("descent_obligations", "projection", (
        pk("descent_obligation_id"),
        col("trace_key"),
        col("from_layer"),
        col("required_layer"),
        col("kind"),
        col("status"),
        col("reason"),
        col("defer_owner"),
        col("defer_spec"),
        col("source"),
        col("indexed_at"),
    )),
    ("screens", "projection", (
        pk("screen_id"),
        col("name"),
        col("category"),
        col("url"),
        col("l1_ref"),
        col("status"),
        col("implemented", "INTEGER"),
        col("indexed_at"),
    )),
    ("screen_trace", "projection", (
        pk("screen_trace_id"),
        col("screen_id"),
        col("requirement_id"),
        col("requirement_kind"),
        col("relation"),
        col("source"),
    )),
)
