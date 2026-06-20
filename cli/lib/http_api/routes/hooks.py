"""HELIX HTTP API — hook callback endpoint.

契約: D-API EXT §3.3 hook callback
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-004 / Sprint .3 (commit a387f9c)
test: cli/lib/tests/test_http_api_hooks.py (5 cases)

責務:
  - POST /api/v1/automation/hooks/{hook_kind}/callback
  - hook_kind enum [pretool, posttool, stop, session_start]
  - audit_log 連携 (hook_exec audit_kind)
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from inspect import signature
from pathlib import Path
from typing import Any

import helix_db
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from cli.lib import compatibility_adapter
compatibility_adapter.helix_db = helix_db

from ..compat import Blueprint, request
from ..envelope import error_response, success_response

bp = Blueprint("hooks", __name__)

VALID_HOOK_KINDS = {"pretool", "posttool", "stop", "session_start"}


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


@bp.route("/api/v1/automation/hooks/<hook_kind>/callback", methods=["POST"])
def hook_callback(hook_kind: str):
    trace_id = request.headers.get("X-Trace-Id", "")
    if hook_kind not in VALID_HOOK_KINDS:
        return error_response("BAD_REQUEST", f"invalid hook_kind: {hook_kind}", trace_id, 400)

    body = _request_json()
    if body.get("hook_kind") != hook_kind:
        return error_response("BAD_REQUEST", "hook_kind mismatch (path vs body)", trace_id, 400)

    run_id = body.get("run_id")
    if not isinstance(run_id, int) or run_id < 1:
        return error_response("BAD_REQUEST", "run_id must be positive integer", trace_id, 400)

    actor = body.get("actor", f"http-hook-{hook_kind}")
    if not isinstance(actor, str) or not actor.strip():
        return error_response("BAD_REQUEST", "actor must be a non-empty string", trace_id, 400)

    payload = body.get("payload", {})
    if not isinstance(payload, dict):
        return error_response("BAD_REQUEST", "payload must be an object", trace_id, 400)

    db_path = helix_db.resolve_default_db_path()
    with _compat_write_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM automation_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if existing is None:
            return error_response("NOT_FOUND", f"automation_runs.id={run_id} not found", trace_id, 404)

        try:
            helix_db.insert_audit_log(
                conn,
                audit_kind="hook_exec",
                actor=actor,
                run_id=run_id,
                payload={"hook_kind": hook_kind, **payload},
            )
        except Exception as exc:
            return error_response("INTERNAL", f"audit_log insert failed: {exc}", trace_id, 500)

    return success_response(
        {"acknowledged": True, "persisted_at": datetime.now(timezone.utc).isoformat()},
        trace_id,
    )
