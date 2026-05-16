"""PLAN-074 single-unit tests for cli/lib/http_api/routes/audit.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §3.4 audit endpoint
- 対象実装 (② D-IMPL): cli/lib/http_api/routes/audit.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.5
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_routes_audit.py
"""

from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from http_api.routes import audit as audit_module
from http_api.server import create_app


@contextmanager
def _managed_connection(conn):
    yield conn


def _auth_headers(trace_id: str = "trace-audit-001") -> dict[str, str]:
    return {
        "Authorization": "Bearer test-token-abc",
        "X-Trace-Id": trace_id,
    }


def _audit_body(
    run_id: int,
    *,
    audit_kind: str = "footer",
    payload: dict[str, object] | None = None,
    actor: str = "cli",
    related_plan_id: str | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "audit_kind": audit_kind,
        "payload": payload or {"summary": "test"},
        "run_id": run_id,
        "actor": actor,
    }
    if related_plan_id is not None:
        body["related_plan_id"] = related_plan_id
    return body


def _configure_audit_db(monkeypatch: pytest.MonkeyPatch, *, run_exists: bool = True):
    fake_conn = MagicMock(name="fake_conn")
    fake_conn.execute.return_value.fetchone.return_value = (1,) if run_exists else None
    insert_spy = MagicMock(name="insert_audit_log")

    monkeypatch.setattr(
        audit_module.helix_db,
        "resolve_default_db_path",
        MagicMock(return_value="/tmp/helix-audit-test.db"),
    )
    monkeypatch.setattr(
        audit_module.helix_db,
        "_write_connection",
        lambda _path: _managed_connection(fake_conn),
    )
    monkeypatch.setattr(audit_module.helix_db, "insert_audit_log", insert_spy)
    return fake_conn, insert_spy


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-abc")
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_request_json_returns_payload_dict():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-H-001 (request.get_json() = {"x": 1} -> {"x": 1})
    対象実装: cli/lib/http_api/routes/audit.py::_request_json
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    req = MagicMock()
    req.get_json.return_value = {"x": 1}
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(audit_module, "request", req)
        assert audit_module._request_json() == {"x": 1}
    finally:
        monkeypatch.undo()


def test_request_json_returns_empty_on_exception():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-H-002 (request.get_json() raises -> {})
    対象実装: cli/lib/http_api/routes/audit.py::_request_json
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    req = MagicMock()
    req.get_json.side_effect = [TypeError("bad call"), {}]
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(audit_module, "request", req)
        assert audit_module._request_json() == {}
    finally:
        monkeypatch.undo()


def test_request_json_returns_empty_on_none():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-H-003 (request.get_json() = None -> {})
    対象実装: cli/lib/http_api/routes/audit.py::_request_json
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    req = MagicMock()
    req.get_json.return_value = None
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(audit_module, "request", req)
        assert audit_module._request_json() == {}
    finally:
        monkeypatch.undo()


def test_http_audit_kinds_accepts_footer():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-V-001 ("footer" is valid)
    対象実装: cli/lib/http_api/routes/audit.py::HTTP_AUDIT_KINDS
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    assert "footer" in audit_module.HTTP_AUDIT_KINDS


def test_http_audit_kinds_accepts_summary():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-V-002 ("summary" is valid)
    対象実装: cli/lib/http_api/routes/audit.py::HTTP_AUDIT_KINDS
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    assert "summary" in audit_module.HTTP_AUDIT_KINDS


def test_http_audit_kinds_rejects_hook_exec():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-V-003 ("hook_exec" is invalid)
    対象実装: cli/lib/http_api/routes/audit.py::HTTP_AUDIT_KINDS
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    assert "hook_exec" not in audit_module.HTTP_AUDIT_KINDS


def test_http_audit_kinds_rejects_empty_string():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-V-004 (empty string is invalid)
    対象実装: cli/lib/http_api/routes/audit.py::HTTP_AUDIT_KINDS
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    assert "" not in audit_module.HTTP_AUDIT_KINDS


def test_http_audit_kinds_rejects_none():
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-V-005 (None is invalid)
    対象実装: cli/lib/http_api/routes/audit.py::HTTP_AUDIT_KINDS
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    assert None not in audit_module.HTTP_AUDIT_KINDS


def test_audit_log_handler_success(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-001 (normal body -> 200 + acknowledged)
    対象実装: cli/lib/http_api/routes/audit.py::audit_log
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    fake_conn, insert_spy = _configure_audit_db(monkeypatch, run_exists=True)
    response = client.post(
        "/api/v1/automation/audit/log",
        headers={**_auth_headers("trace-audit-001"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_audit_body(7, related_plan_id="PLAN-074"),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["data"]["acknowledged"] is True
    assert "persisted_at" in data["data"]
    insert_spy.assert_called_once()
    assert fake_conn.execute.call_count == 1


def test_audit_log_handler_missing_fields_returns_400(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-002 (required field missing -> 400)
    対象実装: cli/lib/http_api/routes/audit.py::audit_log
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    fake_conn, insert_spy = _configure_audit_db(monkeypatch, run_exists=True)
    response = client.post(
        "/api/v1/automation/audit/log",
        headers={**_auth_headers("trace-audit-002"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json={"audit_kind": "footer"},
    )

    assert response.status_code == 400
    assert fake_conn.execute.call_count == 0
    assert insert_spy.call_count == 0


def test_audit_log_handler_run_id_not_found_returns_404(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-003 (run_id missing -> 404)
    対象実装: cli/lib/http_api/routes/audit.py::audit_log
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    _fake_conn, insert_spy = _configure_audit_db(monkeypatch, run_exists=False)
    response = client.post(
        "/api/v1/automation/audit/log",
        headers={**_auth_headers("trace-audit-003"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_audit_body(99999, audit_kind="summary"),
    )

    assert response.status_code == 404
    assert insert_spy.call_count == 0


def test_audit_log_handler_integrity_error_returns_409(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-004 (sqlite IntegrityError -> 409)
    対象実装: cli/lib/http_api/routes/audit.py::audit_log
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    _fake_conn, insert_spy = _configure_audit_db(monkeypatch, run_exists=True)
    insert_spy.side_effect = sqlite3.IntegrityError("conflict")
    response = client.post(
        "/api/v1/automation/audit/log",
        headers={**_auth_headers("trace-audit-004"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_audit_body(7),
    )

    assert response.status_code == 409
    insert_spy.assert_called_once()


def test_audit_log_handler_sqlite_error_returns_500(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-005 (sqlite Error -> 500)
    対象実装: cli/lib/http_api/routes/audit.py::audit_log
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    _fake_conn, insert_spy = _configure_audit_db(monkeypatch, run_exists=True)
    insert_spy.side_effect = sqlite3.Error("db down")
    response = client.post(
        "/api/v1/automation/audit/log",
        headers={**_auth_headers("trace-audit-005"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_audit_body(7),
    )

    assert response.status_code == 500
    insert_spy.assert_called_once()


def test_audit_log_handler_uses_endpoint_call_and_backs_up_payload(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-AUD-006 (payload.http_audit_kind backup and endpoint_call fixed)
    対象実装: cli/lib/http_api/routes/audit.py::audit_log
    対象設計 (①): D-API EXT §3.4 audit endpoint
    """
    _fake_conn, insert_spy = _configure_audit_db(monkeypatch, run_exists=True)
    response = client.post(
        "/api/v1/automation/audit/log",
        headers={**_auth_headers("trace-audit-006"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_audit_body(7, audit_kind="summary", related_plan_id="PLAN-075"),
    )

    assert response.status_code == 200
    assert insert_spy.call_count == 1
    args, kwargs = insert_spy.call_args
    assert kwargs.get("audit_kind", args[0] if args else None) == "endpoint_call"
    payload = kwargs["payload"]
    assert payload["http_audit_kind"] == "summary"
    assert payload["related_plan_id"] == "PLAN-075"
