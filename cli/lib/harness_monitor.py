#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

try:
    from . import agent_slots, compatibility_adapter, helix_db
    from .route_engine import RouteEngine
except ImportError:  # pragma: no cover
    import agent_slots
    import helix_db
    from route_engine import RouteEngine
    REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from cli.lib import compatibility_adapter
    compatibility_adapter.helix_db = helix_db


ALLOWED_EVENT_KINDS = ("pull", "push", "audit")
ALLOWED_SEVERITIES = ("info", "warning", "critical")


@contextmanager
def _compat_write_connection(db_path: str | None = None, ensure_schema: bool = True):
    generator = compatibility_adapter.write_connection.__wrapped__(db_path, ensure_schema)
    conn = next(generator)
    try:
        yield conn
    except BaseException as exc:
        try:
            generator.throw(exc)
        except StopIteration:
            pass
        raise
    else:
        try:
            next(generator)
        except StopIteration:
            pass


@contextmanager
def _read_connection(db_path: str | None = None):
    conn = helix_db.get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def _validate_choice(value: str, field_name: str, allowed_values: tuple[str, ...]) -> str:
    text = str(value).strip()
    if text not in allowed_values:
        raise ValueError(f"invalid {field_name}: {value}")
    return text


def _require_non_empty_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_non_negative_int(value: int, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _encode_payload(payload: dict | None) -> str | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict or None")
    return json.dumps(payload, ensure_ascii=False)


def _decode_payload(value: str | None) -> dict | None:
    if not value:
        return None
    decoded = json.loads(value)
    if decoded is None:
        return None
    if not isinstance(decoded, dict):
        raise ValueError("payload must decode to a dict")
    return decoded


def _row_to_event(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["payload"] = _decode_payload(item.get("payload"))
    item["user_visible"] = bool(item["user_visible"])
    return item


def _fetch_recent_events(
    conn: sqlite3.Connection,
    *,
    days: int,
    severity: str | None,
    session_id: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    where = []
    params: list[object] = []
    if days == 0:
        where.append("triggered_at >= datetime('now', 'start of day')")
    else:
        where.append("triggered_at >= datetime('now', ?)")
        params.append(f"-{days} days")
    if severity is not None:
        where.append("severity = ?")
        params.append(severity)
    if session_id is not None:
        where.append("session_id = ?")
        params.append(session_id)
    limit_sql = ""
    if limit is not None:
        limit_sql = " LIMIT ?"
        params.append(limit)
    rows = conn.execute(
        f"""
        SELECT *
        FROM harness_check_events
        WHERE {' AND '.join(where)}
        ORDER BY triggered_at DESC, id DESC
        {limit_sql}
        """,
        params,
    ).fetchall()
    return [_row_to_event(row) for row in rows]


def _query_running_tasks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, run_kind, trigger_actor, plan_id, started_at, status, summary
        FROM automation_runs
        WHERE status = 'running'
        ORDER BY started_at ASC, id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _query_recent_hook_findings(conn: sqlite3.Connection, *, days: int, limit: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, event_type, file, result, created_at
        FROM hook_events
        WHERE result IN ('warn', 'fail')
          AND created_at >= datetime('now', ?)
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (f"-{days} days", limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _query_recent_harness_findings(conn: sqlite3.Connection, *, days: int, limit: int) -> list[dict]:
    return _fetch_recent_events(conn, days=days, severity="warning", limit=limit) + _fetch_recent_events(
        conn,
        days=days,
        severity="critical",
        limit=limit,
    )


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()
    return int(row["cnt"] if row is not None else 0)


def _count_hook_warn_fail(conn: sqlite3.Connection, days: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM hook_events
        WHERE result IN ('warn', 'fail')
          AND created_at >= datetime('now', ?)
        """,
        (f"-{days} days",),
    ).fetchone()
    return int(row["cnt"] if row is not None else 0)


def _count_harness_warning_critical(conn: sqlite3.Connection, days: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM harness_check_events
        WHERE severity IN ('warning', 'critical')
          AND triggered_at >= datetime('now', ?)
        """,
        (f"-{days} days",),
    ).fetchone()
    return int(row["cnt"] if row is not None else 0)


def _drift_type_from_hook_event(event_type: str) -> str:
    lowered = event_type.lower()
    if "contract" in lowered:
        return "contract"
    if "index" in lowered or "schema" in lowered or "db" in lowered:
        return "schema"
    if "dependency" in lowered:
        return "dependency_outdated"
    return "code_smell"


def _route_candidate(signal: str, *, evidence: dict, drift_type: str | None = None, impact: str = "low") -> dict:
    route = RouteEngine().evaluate(
        signal,
        uncertainty="low",
        impact=impact,
        drift_type=drift_type,
    )
    return {
        "signal": signal,
        "source": evidence.get("source"),
        "evidence": evidence,
        "route": route.to_dict(),
    }


def _target_layer_for_route(route: dict) -> str:
    mode = str(route.get("mode") or "")
    if mode == "Reverse":
        return "L3-L6"
    if mode == "Refactor":
        return "L7-L9"
    if mode in {"Recovery", "recovery", "auto_run"}:
        return "L7-L14"
    if mode in {"Incident", "incident"}:
        return "L11-L14"
    return "L4-L14"


def _plan_candidate_from_route(candidate: dict) -> dict:
    signal = str(candidate.get("signal") or "unknown")
    route = candidate.get("route") if isinstance(candidate.get("route"), dict) else {}
    evidence = candidate.get("evidence") if isinstance(candidate.get("evidence"), dict) else {}
    mode = str(route.get("mode") or "unknown")
    source = str(evidence.get("source") or candidate.get("source") or "unknown")
    evidence_id = evidence.get("id")
    evidence_ref = f"{source}#{evidence_id}" if evidence_id is not None else source
    return {
        "candidate_type": "plan",
        "title": f"L14-feedback-loop-{signal}-plan",
        "source_pattern_key": f"{source}:{signal}:{mode}",
        "problem": {
            "summary": str(route.get("plan_hint") or f"{signal} routed to {mode}"),
            "evidence": [evidence_ref],
            "signal": signal,
        },
        "proposal": {
            "target_layer": _target_layer_for_route(route),
            "scope": ["workflow", "db", "tests"],
            "non_goals": [
                "detector 直接変更",
                "gate 直接変更",
                "schema migration",
                "自動実行",
            ],
        },
        "handoff": {
            "owner_role": "tl",
            "review_required": True,
        },
        "recommended_command": route.get("recommended_command"),
    }


def _pr_candidate_from_learning(candidate: dict) -> dict:
    kind = str(candidate.get("kind") or "unknown")
    source = str(candidate.get("source") or "unknown")
    summary = str(candidate.get("summary") or kind)
    evidence_id = candidate.get("id")
    evidence_ref = f"{source}#{evidence_id}" if evidence_id is not None else source
    return {
        "candidate_type": "pr",
        "title": f"docs: tighten {source} feedback-loop handoff",
        "source_pattern_key": f"{source}:{kind}",
        "change_summary": [
            summary,
            "Add or adjust the existing workflow/runbook/checklist before changing gates or detectors.",
        ],
        "evidence": [evidence_ref],
        "review_gate": {
            "required": True,
            "command": "helix review --uncommitted",
        },
    }


def _missing_input_count(snapshot: dict) -> int:
    learning_candidates = snapshot.get("learning_candidates")
    if not isinstance(learning_candidates, list):
        return 0
    return sum(
        1
        for candidate in learning_candidates
        if isinstance(candidate, dict) and str(candidate.get("kind") or "").startswith("missing_")
    )


def _collect_vg_overview_feedback() -> dict:
    try:
        lib_dir = Path(__file__).resolve().parent
        if str(lib_dir) not in sys.path:
            sys.path.insert(0, str(lib_dir))
        collect_vg_overview = importlib.import_module("vg_overview").collect_vg_overview

        report = collect_vg_overview(strict_full_flow=True, execute_g7_tests=False)
        vg = report.get("vg_overview", {}) if isinstance(report, dict) else {}
        full = vg.get("full_flow_execution", {}) if isinstance(vg, dict) else {}
        return {
            "available": True,
            "overall_clean": bool(vg.get("overall_clean")),
            "enforced": bool(full.get("enforced")),
            "deferred_count": int(full.get("deferred_count") or 0),
            "deferred_pairs": full.get("deferred_pairs") or [],
            "not_applicable_count": int(full.get("not_applicable_count") or 0),
            "not_applicable_pairs": full.get("not_applicable_pairs") or [],
        }
    except Exception as exc:
        return {
            "available": False,
            "error": str(exc),
            "overall_clean": False,
            "enforced": True,
            "deferred_count": 0,
            "deferred_pairs": [],
            "not_applicable_count": 0,
            "not_applicable_pairs": [],
        }


def _query_peak_parallel_today(conn: sqlite3.Connection, session_id: str | None) -> int:
    where = ["fired_at >= datetime('now', 'start of day')"]
    params: list[object] = []
    if session_id is not None:
        where.append("session_id = ?")
        params.append(session_id)
    row = conn.execute(
        f"""
        WITH base AS (
            SELECT
                id,
                fired_at,
                COALESCE(released_at, datetime('now')) AS ended_at
            FROM agent_slots
            WHERE {' AND '.join(where)}
        ),
        overlaps AS (
            SELECT
                a.id,
                (
                    SELECT COUNT(*)
                    FROM base b
                    WHERE b.fired_at <= a.ended_at
                      AND b.ended_at >= a.fired_at
                ) AS concurrent_count
            FROM base a
        )
        SELECT COALESCE(MAX(concurrent_count), 0) AS peak_parallel_today
        FROM overlaps
        """,
        params,
    ).fetchone()
    return int(row["peak_parallel_today"]) if row is not None else 0


# @helix:index id=harness_monitor.record_event domain=cli/lib summary=harness check event を append-only で記録する
def record_event(
    event_kind: str,
    check_name: str,
    *,
    session_id: str | None = None,
    related_slot_id: int | None = None,
    plan_id: str | None = None,
    severity: str = "info",
    payload: dict | None = None,
    user_visible: bool = False,
) -> int:
    """harness check event を INSERT し、row id を返す。"""
    event_kind = _validate_choice(event_kind, "event_kind", ALLOWED_EVENT_KINDS)
    check_name = _require_non_empty_text(check_name, "check_name")
    severity = _validate_choice(severity, "severity", ALLOWED_SEVERITIES)
    if related_slot_id is not None:
        related_slot_id = helix_db._validate_positive_int(related_slot_id, "related_slot_id")
    row = {
        "event_kind": event_kind,
        "check_name": check_name,
        "session_id": _clean_optional_text(session_id),
        "related_slot_id": related_slot_id,
        "plan_id": _clean_optional_text(plan_id),
        "severity": severity,
        "payload": _encode_payload(payload),
        "user_visible": int(bool(user_visible)),
    }
    columns = list(row.keys())
    placeholders = ", ".join(["?"] * len(columns))
    with _compat_write_connection(None) as conn:
        cursor = conn.execute(
            f"INSERT INTO harness_check_events ({', '.join(columns)}) VALUES ({placeholders})",
            [row[column] for column in columns],
        )
        return int(cursor.lastrowid)


# @helix:index id=harness_monitor.get_active_status domain=cli/lib summary=active harness status summary を返す
def get_active_status(session_id: str | None = None) -> dict:
    """active harness status summary を返す。"""
    session_id = _clean_optional_text(session_id)
    active_slots = agent_slots.list_active_slots()
    if session_id is not None:
        active_slots = [slot for slot in active_slots if slot.get("session_id") == session_id]
    with _compat_write_connection(None) as conn:
        return {
            "active_slot_count": len(active_slots),
            "running_tasks": _query_running_tasks(conn),
            "recent_warnings": _fetch_recent_events(
                conn,
                days=1,
                severity="warning",
                session_id=session_id,
                limit=10,
            ),
            "recent_criticals": _fetch_recent_events(
                conn,
                days=1,
                severity="critical",
                session_id=session_id,
                limit=10,
            ),
            "peak_parallel_today": _query_peak_parallel_today(conn, session_id),
        }


# @helix:index id=harness_monitor.get_session_audit domain=cli/lib summary=session 単位の harness event audit summary を返す
def get_session_audit(session_id: str) -> dict:
    """session 単位の harness event audit summary を返す。"""
    session_id = _require_non_empty_text(session_id, "session_id")
    with _compat_write_connection(None) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                COALESCE(SUM(CASE WHEN event_kind = 'pull' THEN 1 ELSE 0 END), 0) AS pull_count,
                COALESCE(SUM(CASE WHEN event_kind = 'push' THEN 1 ELSE 0 END), 0) AS push_count,
                COALESCE(SUM(CASE WHEN event_kind = 'audit' THEN 1 ELSE 0 END), 0) AS audit_count,
                COALESCE(SUM(CASE WHEN severity = 'info' THEN 1 ELSE 0 END), 0) AS info_count,
                COALESCE(SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END), 0) AS warning_count,
                COALESCE(SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END), 0) AS critical_count,
                MIN(triggered_at) AS first_event_at,
                MAX(triggered_at) AS last_event_at
            FROM harness_check_events
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        total_events = int(row["total_events"]) if row is not None else 0
        return {
            "session_id": session_id,
            "total_events": total_events,
            "by_kind": {
                "pull": int(row["pull_count"]) if row is not None else 0,
                "push": int(row["push_count"]) if row is not None else 0,
                "audit": int(row["audit_count"]) if row is not None else 0,
            },
            "by_severity": {
                "info": int(row["info_count"]) if row is not None else 0,
                "warning": int(row["warning_count"]) if row is not None else 0,
                "critical": int(row["critical_count"]) if row is not None else 0,
            },
            "first_event_at": row["first_event_at"] if row is not None else None,
            "last_event_at": row["last_event_at"] if row is not None else None,
        }


# @helix:index id=harness_monitor.list_recent_events domain=cli/lib summary=直近 N 日の harness event 一覧を返す
def list_recent_events(days: int = 1, severity: str | None = None) -> list[dict]:
    """直近 N 日の harness event 一覧を返す。"""
    days = _validate_non_negative_int(days, "days")
    if severity is not None:
        severity = _validate_choice(severity, "severity", ALLOWED_SEVERITIES)
    with _compat_write_connection(None) as conn:
        return _fetch_recent_events(conn, days=days, severity=severity)


# @helix:index id=harness_monitor.get_feedback_loop_snapshot domain=cli/lib summary=既存DB入力から route / learning candidate を生成する
def get_feedback_loop_snapshot(days: int = 7, limit: int = 20) -> dict:
    """既存 DB 入力だけで feedback loop の route / learning candidate を返す。

    schema migration や自動実行は行わない。DB に蓄積済みの hook / harness /
    automation / feedback / observe / verify 入力を読み、後続 PLAN draft の材料にする。
    """
    days = _validate_non_negative_int(days, "days")
    limit = _validate_non_negative_int(limit, "limit")
    if limit == 0:
        limit = 20

    with _read_connection(None) as conn:
        running_tasks = _query_running_tasks(conn)
        hook_findings = _query_recent_hook_findings(conn, days=days, limit=limit)
        harness_findings = sorted(
            _query_recent_harness_findings(conn, days=days, limit=limit),
            key=lambda item: ((item.get("triggered_at") or ""), int(item.get("id") or 0)),
            reverse=True,
        )[:limit]
        counts = {
            "automation_running": len(running_tasks),
            "hook_warn_fail": _count_hook_warn_fail(conn, days),
            "harness_warning_critical": _count_harness_warning_critical(conn, days),
            "feedback": _count_rows(conn, "feedback"),
            "events": _count_rows(conn, "events"),
            "metrics": _count_rows(conn, "metrics"),
            "verify_runs": _count_rows(conn, "verify_runs"),
        }

        feedback_rows = conn.execute(
            """
            SELECT id, feedback_type, category, description, impact, created_at
            FROM feedback
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    route_candidates: list[dict] = []
    for task in running_tasks[:limit]:
        route_candidates.append(
            _route_candidate(
                "long_running_task",
                impact="high",
                evidence={
                    "source": "automation_runs",
                    "id": task.get("id"),
                    "plan_id": task.get("plan_id"),
                    "run_kind": task.get("run_kind"),
                    "started_at": task.get("started_at"),
                    "status": task.get("status"),
                },
            )
        )

    for finding in hook_findings[:limit]:
        drift_type = _drift_type_from_hook_event(str(finding.get("event_type") or ""))
        route_candidates.append(
            _route_candidate(
                "drift",
                drift_type=drift_type,
                impact="high",
                evidence={
                    "source": "hook_events",
                    "id": finding.get("id"),
                    "event_type": finding.get("event_type"),
                    "file": finding.get("file"),
                    "result": finding.get("result"),
                    "created_at": finding.get("created_at"),
                },
            )
        )

    for finding in harness_findings[:limit]:
        route_candidates.append(
            _route_candidate(
                "regression_dev",
                evidence={
                    "source": "harness_check_events",
                    "id": finding.get("id"),
                    "check_name": finding.get("check_name"),
                    "severity": finding.get("severity"),
                    "triggered_at": finding.get("triggered_at"),
                    "payload": finding.get("payload"),
                },
            )
        )

    learning_candidates: list[dict] = []
    if counts["feedback"] == 0:
        learning_candidates.append(
            {
                "kind": "missing_feedback_input",
                "source": "feedback",
                "summary": "feedback table is empty; gate/user feedback is not yet available to learning-engine",
            }
        )
    else:
        for row in feedback_rows:
            learning_candidates.append(
                {
                    "kind": "feedback_pattern",
                    "source": "feedback",
                    "id": row["id"],
                    "category": row["category"],
                    "impact": row["impact"],
                    "summary": row["description"],
                }
            )
    if counts["events"] == 0 and counts["metrics"] == 0:
        learning_candidates.append(
            {
                "kind": "missing_observability_input",
                "source": "events/metrics",
                "summary": "observe events and metrics are empty; operational signals cannot yet drive learning",
            }
        )
    if counts["verify_runs"] == 0:
        learning_candidates.append(
            {
                "kind": "missing_verify_input",
                "source": "verify_runs",
                "summary": "verify_runs is empty; verification closure is not yet available to learning-engine",
            }
        )
    if counts["hook_warn_fail"] > 0:
        learning_candidates.append(
            {
                "kind": "detector_pattern",
                "source": "hook_events",
                "summary": f"{counts['hook_warn_fail']} warn/fail hook events detected in the last {days} days",
            }
        )
    if counts["harness_warning_critical"] > 0:
        learning_candidates.append(
            {
                "kind": "harness_warning_pattern",
                "source": "harness_check_events",
                "summary": f"{counts['harness_warning_critical']} warning/critical harness events detected in the last {days} days",
            }
        )
    if counts["automation_running"] > 0:
        learning_candidates.append(
            {
                "kind": "automation_running_pattern",
                "source": "automation_runs",
                "summary": f"{counts['automation_running']} automation run(s) still marked running",
            }
        )
    vg_feedback = _collect_vg_overview_feedback()
    if vg_feedback["available"]:
        for pair in vg_feedback["deferred_pairs"]:
            if not isinstance(pair, dict):
                continue
            learning_candidates.append(
                {
                    "kind": "full_flow_deferred_execution_gate",
                    "source": "vg_overview",
                    "pair": pair.get("pair"),
                    "gate_id": pair.get("gate_id"),
                    "target": pair.get("target"),
                    "summary": (
                        f"{pair.get('pair')} remains deferred for {pair.get('gate_id')}; "
                        f"{pair.get('next_action')}"
                    ),
                }
            )
        for pair in vg_feedback["not_applicable_pairs"]:
            if not isinstance(pair, dict):
                continue
            waiver = pair.get("waiver") if isinstance(pair.get("waiver"), dict) else {}
            learning_candidates.append(
                {
                    "kind": "not_applicable_pair_waiver",
                    "source": "vg_overview",
                    "pair": pair.get("pair"),
                    "reason": waiver.get("reason"),
                    "owner": waiver.get("owner"),
                    "summary": (
                        f"{pair.get('pair')} is not_applicable by {waiver.get('reason')} "
                        f"waiver owned by {waiver.get('owner')}"
                    ),
                }
            )
    plan_candidates = [_plan_candidate_from_route(candidate) for candidate in route_candidates[:limit]]
    pr_candidates = [_pr_candidate_from_learning(candidate) for candidate in learning_candidates[:limit]]

    return {
        "schema_version": "helix_harness_feedback_loop_snapshot_v1",
        "window_days": days,
        "counts": counts,
        "vg_overview": vg_feedback,
        "route_candidates": route_candidates[:limit],
        "learning_candidates": learning_candidates[:limit],
        "plan_candidates": plan_candidates,
        "pr_candidates": pr_candidates,
        "safety": {
            "schema_migration": False,
            "auto_apply": False,
            "writes_detector_or_gate": False,
        },
    }


# @helix:index id=harness_monitor.record_feedback_loop_observability domain=cli/lib summary=feedback-loop snapshot を events/metrics に登録する
def record_feedback_loop_observability(snapshot: dict, db_path: str | None = None) -> dict:
    """feedback-loop snapshot の要約を既存 events / metrics に append する。"""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a dict")
    route_count = len(snapshot.get("route_candidates") or [])
    learning_count = len(snapshot.get("learning_candidates") or [])
    plan_count = len(snapshot.get("plan_candidates") or [])
    pr_count = len(snapshot.get("pr_candidates") or [])
    missing_count = _missing_input_count(snapshot)
    vg_overview = snapshot.get("vg_overview") if isinstance(snapshot.get("vg_overview"), dict) else {}
    full_flow_deferred_count = int(vg_overview.get("deferred_count") or 0)
    not_applicable_count = int(vg_overview.get("not_applicable_count") or 0)
    severity = "warning" if route_count or missing_count else "info"
    event_id = helix_db.insert_event(
        db_path,
        "harness.feedback_loop.snapshot",
        {
            "schema_version": snapshot.get("schema_version"),
            "window_days": snapshot.get("window_days"),
            "counts": snapshot.get("counts") or {},
            "route_candidates": route_count,
            "learning_candidates": learning_count,
            "plan_candidates": plan_count,
            "pr_candidates": pr_count,
            "missing_inputs": missing_count,
            "vg_overview": vg_overview,
            "safety": snapshot.get("safety") or {},
        },
        source="helix-harness",
        severity=severity,
    )
    metric_ids = {
        "route_candidates": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.route_candidates",
            route_count,
            tags={"source": "helix-harness"},
        ),
        "learning_candidates": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.learning_candidates",
            learning_count,
            tags={"source": "helix-harness"},
        ),
        "plan_candidates": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.plan_candidates",
            plan_count,
            tags={"source": "helix-harness"},
        ),
        "pr_candidates": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.pr_candidates",
            pr_count,
            tags={"source": "helix-harness"},
        ),
        "missing_inputs": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.missing_inputs",
            missing_count,
            tags={"source": "helix-harness"},
        ),
        "full_flow_deferred_gates": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.full_flow_deferred_gates",
            full_flow_deferred_count,
            tags={"source": "helix-harness"},
        ),
        "not_applicable_pairs": helix_db.insert_metric(
            db_path,
            "harness.feedback_loop.not_applicable_pairs",
            not_applicable_count,
            tags={"source": "helix-harness"},
        ),
    }
    return {
        "event_id": event_id,
        "metric_ids": metric_ids,
        "severity": severity,
    }


# @helix:index id=harness_monitor.record_feedback_loop_missing_feedback domain=cli/lib summary=missing feedback input を feedback table に自動登録する
def record_feedback_loop_missing_feedback(snapshot: dict, db_path: str | None = None) -> dict:
    """feedback 入力が空の場合だけ、既存 feedback table に運用 feedback を append する。"""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a dict")
    counts = snapshot.get("counts") if isinstance(snapshot.get("counts"), dict) else {}
    if int(counts.get("feedback") or 0) > 0:
        return {"recorded": False, "reason": "feedback_already_exists", "feedback_id": None}
    has_missing_feedback = any(
        isinstance(candidate, dict) and candidate.get("kind") == "missing_feedback_input"
        for candidate in (snapshot.get("learning_candidates") or [])
    )
    if not has_missing_feedback:
        return {"recorded": False, "reason": "missing_feedback_input_not_detected", "feedback_id": None}

    description = (
        "feedback-loop snapshot detected empty feedback input; "
        "connect gate/user feedback or review output to learning-engine"
    )
    with _compat_write_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback (task_run_id, feedback_type, category, description, impact, resolution)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                None,
                "suggestion",
                "missing-action",
                description,
                "medium",
                "harness-feedback-loop-auto-registered",
            ),
        )
        feedback_id = int(cursor.lastrowid)
    return {"recorded": True, "reason": "missing_feedback_input", "feedback_id": feedback_id}
