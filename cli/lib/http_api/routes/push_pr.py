"""HELIX HTTP API — push / pr trigger endpoint.

契約: D-API EXT §3.1 push trigger + §3.2 pr trigger
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-003 / Sprint .2 (commit 95cb7be)
test: cli/lib/tests/test_http_api_push_pr.py (5 cases)

責務:
  - POST /api/v1/automation/push/{plan_id}/trigger
  - POST /api/v1/automation/pr/{plan_id}/trigger
  - push_gate.run_all_gates() 結合 + automation_runs INSERT + audit_log
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from inspect import signature
from pathlib import Path
from typing import Any

try:
    from flask import Blueprint, request
    _HAS_FLASK = True
except ModuleNotFoundError:  # pragma: no cover - exercised in the current sandbox
    _HAS_FLASK = False
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

    def _extract_route_args(pattern: str, path: str) -> list[str] | None:
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return None
        route_args: list[str] = []
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("<") and pattern_part.endswith(">"):
                if not path_part:
                    return None
                route_args.append(path_part)
                continue
            if pattern_part != path_part:
                return None
        return route_args

    if not getattr(server_module.Flask, "_helix_blueprint_routes_patched", False):
        def _register_blueprint(self, blueprint):  # type: ignore[override]
            self._routes.update(getattr(blueprint, "_routes", {}))
            return None

        server_module.Flask.register_blueprint = _register_blueprint
        server_module.Flask._helix_blueprint_routes_patched = True

    if not hasattr(server_module._CompatClient, "post"):
        def _post(self, path: str, headers=None, environ_base=None, json=None, query_string=None):  # type: ignore[override]
            request.path = path
            request.method = "POST"
            request.remote_addr = (environ_base or {}).get("REMOTE_ADDR", "127.0.0.1")
            request.headers = dict(headers or {})
            request.args = dict(query_string or {})
            request._json_payload = json

            def _get_json(silent: bool = True):
                return getattr(request, "_json_payload", None)

            request.get_json = _get_json  # type: ignore[attr-defined]

            if self.app._before_request is not None:
                gate_result = self.app._before_request()
                if gate_result is not None:
                    normalize = getattr(server_module, "_normalize_response", None)
                    return normalize(gate_result) if normalize is not None else gate_result

            route = self.app._routes.get((path, "POST"))
            route_args: list[str] = []
            if route is None:
                for (route_path, method), candidate in self.app._routes.items():
                    if method != "POST":
                        continue
                    matched_args = _extract_route_args(route_path, path)
                    if matched_args is not None:
                        route = candidate
                        route_args = matched_args
                        break
            if route is None:
                handler = self.app._errorhandlers.get(404)
                result = handler(None) if handler is not None else ("not found", 404)
                normalize = getattr(server_module, "_normalize_response", None)
                return normalize(result) if normalize is not None else result

            result = route(*route_args)
            normalize = getattr(server_module, "_normalize_response", None)
            return normalize(result) if normalize is not None else result

        server_module._CompatClient.post = _post

import helix_db
import push_gate
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from cli.lib import compatibility_adapter
compatibility_adapter.helix_db = helix_db

from ..envelope import error_response, success_response


bp = Blueprint("push_pr", __name__)


@contextmanager
def _compat_write_connection(db_path: str | None):
    write_connection = getattr(helix_db, "_write_connection")
    if "ensure_schema" not in signature(write_connection).parameters:
        with write_connection(db_path) as conn:
            yield conn
        return
    with compatibility_adapter.write_connection(db_path) as conn:
        yield conn


def _project_root() -> Path:
    return Path(os.environ.get("HELIX_PROJECT_ROOT") or Path.cwd()).resolve()


def _request_args() -> dict[str, Any]:
    args = getattr(request, "args", None)
    if args is None:
        return {}
    if hasattr(args, "to_dict"):
        try:
            return args.to_dict(flat=True)
        except TypeError:
            return dict(args)
    return dict(args)


def _request_json() -> dict[str, Any]:
    getter = getattr(request, "get_json", None)
    if not callable(getter):
        return {}
    try:
        payload = getter(silent=True)
    except TypeError:
        payload = getter()
    return payload if isinstance(payload, dict) else {}


def _parse_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return None


def _plan_exists(project_root: Path, plan_id: str) -> bool:
    if not plan_id or len(plan_id) > 64:
        return False

    helix_plan = project_root / ".helix" / "plans" / f"{plan_id}.yaml"
    if helix_plan.is_file():
        return True

    docs_plans = project_root / "docs" / "plans"
    if docs_plans.is_dir():
        for candidate in docs_plans.iterdir():
            if candidate.is_file() and candidate.name.startswith(plan_id):
                return True
    return False


def _finalize_response(
    run_id: int,
    gate_result: dict[str, Any],
    execute_requested: bool,
    remote: str,
    branch: str,
    final_status: str,
    trace_id: str,
):
    data = {
        "run_id": run_id,
        "ok": bool(gate_result.get("ok", False)),
        "failed_count": int(gate_result.get("failed_count", 0) or 0),
        "gate_results": gate_result.get("gates", []),
        "execute_requested": execute_requested,
        "remote": remote,
        "branch": branch,
        "push": gate_result.get("push", {"attempted": False, "ok": False, "detail": ""}),
        "pair_transition": {"from": "running", "to": final_status},
    }
    return success_response(data, trace_id)


def _handle_trigger(run_kind: str, trigger_source: str, plan_id: str):
    trace_id = request.headers.get("X-Trace-Id", "")
    if not plan_id or len(plan_id) > 64:
        return error_response("BAD_REQUEST", "plan_id required (1-64 chars)", trace_id, 400)

    project_root = _project_root()
    if not _plan_exists(project_root, plan_id):
        return error_response("NOT_FOUND", f"plan not found: {plan_id}", trace_id, 404)

    body = _request_json()
    required = ["commit_sha", "branch", "trigger_actor", "execute"]
    missing = [key for key in required if key not in body]
    if missing:
        return error_response("BAD_REQUEST", f"missing fields: {missing}", trace_id, 400)

    commit_sha = body["commit_sha"]
    if not isinstance(commit_sha, str) or not (7 <= len(commit_sha) <= 64):
        return error_response("BAD_REQUEST", "commit_sha must be 7-64 char string", trace_id, 400)

    branch = body["branch"]
    if not isinstance(branch, str) or not branch.strip():
        return error_response("BAD_REQUEST", "branch must be a non-empty string", trace_id, 400)

    trigger_actor = body["trigger_actor"]
    if not isinstance(trigger_actor, str) or not trigger_actor.strip():
        return error_response("BAD_REQUEST", "trigger_actor must be a non-empty string", trace_id, 400)

    execute = body["execute"]
    if not isinstance(execute, bool):
        return error_response("BAD_REQUEST", "execute must be a boolean", trace_id, 400)

    remote = body.get("remote", "origin")
    if not isinstance(remote, str) or not remote.strip():
        return error_response("BAD_REQUEST", "remote must be a non-empty string", trace_id, 400)

    args = _request_args()
    force = _parse_bool(args.get("force"))
    dry_run = _parse_bool(args.get("dry_run"))
    if "force" in args and force is None:
        return error_response("BAD_REQUEST", "force must be a boolean", trace_id, 400)
    if "dry_run" in args and dry_run is None:
        return error_response("BAD_REQUEST", "dry_run must be a boolean", trace_id, 400)

    effective_execute = execute if not dry_run else False

    metadata = {
        "trigger_source": trigger_source,
        "plan_id": plan_id,
        "commit_sha": commit_sha,
        "branch": branch,
        "trigger_actor": trigger_actor,
        "execute": effective_execute,
        "remote": remote,
        "force": force,
        "dry_run": dry_run,
    }

    db_path = helix_db.resolve_default_db_path()
    try:
        with _compat_write_connection(db_path) as conn:
            run_id = helix_db.insert_automation_run(
                conn,
                trigger_source=trigger_source,
                run_kind=run_kind,
                metadata=metadata,
            )
    except ValueError as exc:
        return error_response("BAD_REQUEST", str(exc), trace_id, 400)
    except Exception as exc:
        return error_response("CONFLICT", f"automation_runs insert failed: {exc}", trace_id, 409)

    try:
        gate_result = push_gate.run_all_gates(execute=effective_execute, remote=remote, branch=branch)
        if not isinstance(gate_result, dict):
            raise TypeError("gate result must be a dict")
    except Exception as exc:
        with _compat_write_connection(db_path) as conn:
            try:
                helix_db.complete_automation_run(conn, run_id, status="failed", error=str(exc))
            except Exception:
                pass
        return error_response("INTERNAL", f"gate execution failed: {exc}", trace_id, 500)

    final_status = "completed" if gate_result.get("ok") else "failed"
    actor = "http-push" if run_kind == "push" else "http-pr"

    try:
        with _compat_write_connection(db_path) as conn:
            helix_db.complete_automation_run(conn, run_id, status=final_status)
            # NOTE: D-API EXT の audit_kind enum drift は Sprint .4 で解消予定のため hook_exec を継続する。
            helix_db.insert_audit_log(
                conn,
                audit_kind="hook_exec",
                actor=actor,
                run_id=run_id,
                payload={
                    "plan_id": plan_id,
                    "gate_ok": gate_result.get("ok"),
                    "trigger_source": trigger_source,
                },
            )
    except Exception as exc:
        return error_response("CONFLICT", f"automation run finalize failed: {exc}", trace_id, 409)

    return _finalize_response(
        run_id,
        gate_result,
        effective_execute,
        remote,
        branch,
        final_status,
        trace_id,
    )


@bp.route("/api/v1/automation/push/<plan_id>/trigger", methods=["POST"])
def push_trigger(plan_id: str):
    return _handle_trigger("push", "helix-http-push", plan_id)


@bp.route("/api/v1/automation/pr/<plan_id>/trigger", methods=["POST"])
def pr_trigger(plan_id: str):
    return _handle_trigger("pr", "helix-http-pr", plan_id)
