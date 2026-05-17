# @helix:index id=http-api.routes.audit domain=cli/lib/http_api summary=audit/log endpoint (PLAN-074 Sprint .4)
"""HELIX HTTP API — audit endpoint.

契約: D-API EXT §3.4 audit endpoint
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-005 / Sprint .4 (commit 2505c4a)
test: cli/lib/tests/test_http_api_audit.py (5 cases)

責務:
  - POST /api/v1/automation/audit/log
  - HTTP audit_kind enum [footer, summary, diff_lines, security_scan, qa_check]
  - audit_kind enum drift 解決:
    HTTP 側 kind を payload.http_audit_kind に退避し、
    helix_db.insert_audit_log には endpoint_call 固定で記録する
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

import sqlite3

import helix_db
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from cli.lib import compatibility_adapter
compatibility_adapter.helix_db = helix_db

from ..envelope import error_response, success_response

bp = Blueprint("audit", __name__)

HTTP_AUDIT_KINDS = ("footer", "summary", "diff_lines", "security_scan", "qa_check")


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


# @helix:index id=http-api.routes.audit.log domain=cli/lib/http_api summary=audit/log POST handler (HTTP audit_kind を payload.http_audit_kind に退避)
@bp.route("/api/v1/automation/audit/log", methods=["POST"])
def audit_log():
    trace_id = request.headers.get("X-Trace-Id", "")
    if not trace_id or len(trace_id) < 8:
        return error_response("BAD_REQUEST", "X-Trace-Id required (>=8 chars)", trace_id, 400)

    body = _request_json()
    required = ["audit_kind", "payload", "run_id", "actor"]
    missing = [key for key in required if key not in body]
    if missing:
        return error_response("BAD_REQUEST", f"missing fields: {missing}", trace_id, 400)

    audit_kind = body.get("audit_kind")
    if not isinstance(audit_kind, str) or audit_kind not in HTTP_AUDIT_KINDS:
        return error_response(
            "BAD_REQUEST",
            f"audit_kind must be one of {HTTP_AUDIT_KINDS}",
            trace_id,
            400,
        )

    payload_in = body.get("payload")
    if not isinstance(payload_in, dict):
        return error_response("BAD_REQUEST", "payload must be object", trace_id, 400)

    run_id = body.get("run_id")
    if not isinstance(run_id, int) or run_id <= 0:
        return error_response("BAD_REQUEST", "run_id must be positive integer", trace_id, 400)

    actor = body.get("actor")
    if not isinstance(actor, str) or not (1 <= len(actor) <= 128):
        return error_response("BAD_REQUEST", "actor must be 1-128 chars", trace_id, 400)

    related_plan_id = body.get("related_plan_id")
    if related_plan_id is not None and not isinstance(related_plan_id, str):
        return error_response("BAD_REQUEST", "related_plan_id must be string", trace_id, 400)

    db_payload = dict(payload_in)
    db_payload["http_audit_kind"] = audit_kind
    if related_plan_id is not None:
        db_payload.setdefault("related_plan_id", related_plan_id)

    db_path = helix_db.resolve_default_db_path()
    try:
        with _compat_write_connection(db_path) as conn:
            row = conn.execute(
                "SELECT id FROM automation_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
            if row is None:
                return error_response(
                    "NOT_FOUND",
                    f"automation_run not found: run_id={run_id}",
                    trace_id,
                    404,
                )

            helix_db.insert_audit_log(
                conn,
                audit_kind="endpoint_call",
                actor=actor,
                run_id=run_id,
                payload=db_payload,
            )
    except sqlite3.IntegrityError as exc:
        return error_response("CONFLICT", f"audit_log insert conflict: {exc}", trace_id, 409)
    except sqlite3.Error as exc:
        return error_response("INTERNAL", f"db error: {exc}", trace_id, 500)

    persisted_at = datetime.now(timezone.utc).isoformat()
    return success_response(
        {"acknowledged": True, "persisted_at": persisted_at},
        trace_id,
    )
