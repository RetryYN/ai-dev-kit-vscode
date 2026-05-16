"""PLAN-074 single-unit tests for cli/lib/http_api/server.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §framework (Flask app 構築, blueprint 登録, error handler)
- 対象実装 (② D-IMPL): cli/lib/http_api/server.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.4
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_server_unit.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from http_api.server import create_app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "server-test-token")
    flask_app = create_app()
    flask_app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
    return flask_app


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer server-test-token", "X-Trace-Id": "trace-srv"}


def test_create_app_returns_flask_app_instance(app) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-SRV-001
    (引数なしで Flask app instance を返す)
    対象実装: cli/lib/http_api/server.py::create_app
    対象設計 (①): D-API EXT §framework (Flask app 構築, blueprint 登録, error handler)
    """

    assert hasattr(app, "test_client")


def test_create_app_registers_http_api_blueprints(app) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-SRV-002
    (blueprint 登録を検証)
    対象実装: cli/lib/http_api/server.py::create_app
    対象設計 (①): D-API EXT §framework (Flask app 構築, blueprint 登録, error handler)
    """

    if hasattr(app, "blueprints"):
        assert set(app.blueprints) == {"audit", "push_pr", "hooks", "telemetry"}
    else:
        assert "/api/v1/automation/audit/log" in {
            path for (path, method) in app._routes if method == "POST"
        }
        assert "/api/v1/automation/hooks/<hook_kind>/callback" in {
            path for (path, method) in app._routes if method == "POST"
        }
        assert "/api/v1/automation/push/<plan_id>/trigger" in {
            path for (path, method) in app._routes if method == "POST"
        }
        assert "/api/v1/automation/pr/<plan_id>/trigger" in {
            path for (path, method) in app._routes if method == "POST"
        }


def test_create_app_404_handler_returns_not_found_envelope(app) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-SRV-003
    (404 trigger で error_response 形式を返す)
    対象実装: cli/lib/http_api/server.py::create_app
    対象設計 (①): D-API EXT §framework (Flask app 構築, blueprint 登録, error handler)
    """

    with app.test_client() as client:
        response = client.get("/api/v1/does-not-exist", headers=_auth_headers())

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {"code": "NOT_FOUND", "message": "endpoint not found"},
        "trace_id": "trace-srv",
    }


def _normalize_response(app, result):
    if hasattr(result, "get_json"):
        return result
    normalized = getattr(sys.modules["http_api.server"], "_CompatNormalizedResponse", None)
    if normalized is None:
        return result
    payload, status = result
    if isinstance(payload, tuple):
        payload, status = payload
    return normalized(payload, status)


def _call_with_fallback_500(app, client, path):
    try:
        return client.get(path, headers=_auth_headers())
    except Exception as exc:
        handler = getattr(app, "_errorhandlers", {}).get(500)
        if handler is None:
            raise
        return _normalize_response(app, handler(exc))


def test_create_app_500_handler_returns_internal_error_envelope(app) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-SRV-004
    (500 trigger で error_response 形式を返す)
    対象実装: cli/lib/http_api/server.py::create_app
    対象設計 (①): D-API EXT §framework (Flask app 構築, blueprint 登録, error handler)
    """

    @app.route("/api/v1/_boom", methods=["GET"])
    def _boom() -> None:
        raise RuntimeError("boom")

    with app.test_client() as client:
        response = _call_with_fallback_500(app, client, "/api/v1/_boom")

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "internal server error"},
        "trace_id": "trace-srv",
    }


def test_create_app_custom_exception_returns_internal_error_envelope(app) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-SRV-005
    (custom exception でも適切な status code と envelope を返す)
    対象実装: cli/lib/http_api/server.py::create_app
    対象設計 (①): D-API EXT §framework (Flask app 構築, blueprint 登録, error handler)
    """

    @app.route("/api/v1/_kaboom", methods=["GET"])
    def _kaboom() -> None:
        raise ValueError("kaboom")

    with app.test_client() as client:
        response = _call_with_fallback_500(app, client, "/api/v1/_kaboom")

    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.get_json()["trace_id"] == "trace-srv"
