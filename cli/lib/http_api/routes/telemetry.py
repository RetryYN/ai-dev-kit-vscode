"""HELIX HTTP API — session telemetry endpoint.

契約: D-API EXT §3.5 Stop hook telemetry endpoint
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-006 / Sprint .5 (commit 1633202)
test: cli/lib/tests/test_http_api_telemetry.py (5 cases)

責務:
  - POST /api/v1/automation/session/telemetry
  - session_telemetry UPSERT (session_id UNIQUE、v27 schema)
  - tool_uses_count / tokens_total / cost_usd 累積
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from inspect import signature
from pathlib import Path
from typing import Any

try:
    from flask import Blueprint, request
except ModuleNotFoundError:  # pragma: no cover - exercised in the current sandbox
    from ..server import request

    class Blueprint:  # type: ignore[override]
        def __init__(self, name: str, import_name: str) -> None:
            self.name = name
            self.import_name = import_name
            self._routes: dict[tuple[str, str], Any] = {}

        def route(self, path: str, methods=None):
            method_list = methods or ["GET"]

            def decorator(func):
                for method in method_list:
                    self._routes[(path, method.upper())] = func
                return func

            return decorator

    from .. import server as server_module

    if not getattr(server_module.Flask, "_helix_blueprint_routes_patched", False):
        def _register_blueprint(self, blueprint):  # type: ignore[override]
            self._routes.update(getattr(blueprint, "_routes", {}))
            return None

        server_module.Flask.register_blueprint = _register_blueprint
        server_module.Flask._helix_blueprint_routes_patched = True

import helix_db
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from cli.lib import compatibility_adapter
compatibility_adapter.helix_db = helix_db

from ..envelope import error_response, success_response

bp = Blueprint("telemetry", __name__)


@contextmanager
def _compat_write_connection(db_path: str | None):
    write_connection = getattr(helix_db, "_write_connection")
    if "ensure_schema" not in signature(write_connection).parameters:
        with write_connection(db_path) as conn:
            yield conn
        return
    with compatibility_adapter.write_connection(db_path) as conn:
        yield conn


def _request_json() -> dict[str, Any]:
    getter = getattr(request, "get_json", None)
    if not callable(getter):
        return {}
    try:
        payload = getter(silent=True)
    except TypeError:
        payload = getter()
    return payload if isinstance(payload, dict) else {}


def _require_non_empty_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not (1 <= len(value.strip()) <= 128):
        raise ValueError(f"{field_name} must be 1-128 chars")
    return value.strip()


def _require_timestamp_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@bp.route("/api/v1/automation/session/telemetry", methods=["POST"])
def session_telemetry():
    trace_id = request.headers.get("X-Trace-Id", "")
    body = _request_json()

    required = ["run_id", "session_id", "started_at", "ended_at", "model", "role"]
    missing = [key for key in required if key not in body]
    if missing:
        return error_response("BAD_REQUEST", f"missing fields: {missing}", trace_id, 400)

    run_id = body["run_id"]
    if not isinstance(run_id, int) or run_id < 1:
        return error_response("BAD_REQUEST", "run_id must be positive integer", trace_id, 400)

    try:
        session_id = _require_non_empty_string(body["session_id"], "session_id")
        started_at = _require_timestamp_string(body["started_at"], "started_at")
        ended_at = _require_timestamp_string(body["ended_at"], "ended_at")
        model = _require_non_empty_string(body["model"], "model")
        role = _require_non_empty_string(body["role"], "role")
        related_plan_id = _require_non_empty_string(body.get("related_plan_id"), "related_plan_id")
    except ValueError as exc:
        return error_response("BAD_REQUEST", str(exc), trace_id, 400)

    tokens_used = body.get("tokens_used", 0)
    if not isinstance(tokens_used, int) or tokens_used < 0:
        return error_response("BAD_REQUEST", "tokens_used must be integer >= 0", trace_id, 400)

    cost_usd = body.get("cost_usd", 0.0)
    if not isinstance(cost_usd, (int, float)) or cost_usd < 0:
        return error_response("BAD_REQUEST", "cost_usd must be number >= 0", trace_id, 400)
    cost_usd = float(cost_usd)

    db_path = helix_db.resolve_default_db_path()
    with _compat_write_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM automation_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if existing is None:
            return error_response("NOT_FOUND", f"automation_runs.id={run_id} not found", trace_id, 404)

        actor = f"{role}/{model}"
        payload: dict[str, Any] = {
            "session_id": session_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "actor": actor,
            "tool_uses_count": 0,
            "tokens_total": tokens_used,
            "cost_usd": cost_usd,
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if related_plan_id is not None:
            payload["related_plan_id"] = related_plan_id

        try:
            helix_db._upsert_row(conn, "session_telemetry", payload, conflict_column="session_id")
        except Exception as exc:
            return error_response("INTERNAL", f"session_telemetry upsert failed: {exc}", trace_id, 500)

    return success_response(
        {"acknowledged": True, "persisted_at": datetime.now(timezone.utc).isoformat()},
        trace_id,
    )
