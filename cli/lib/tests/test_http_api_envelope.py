"""PLAN-074 single-unit tests for cli/lib/http_api/envelope.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §共通 Envelope schema
- 対象実装 (② D-IMPL): cli/lib/http_api/envelope.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.2
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_envelope.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from http_api.envelope import error_response, success_response


def _normalize_response(result):
    if result is None:
        return None, None
    if isinstance(result, tuple):
        response, status = result
    else:
        response = result
        status = getattr(result, "status_code", None)
    payload = response.get_json() if hasattr(response, "get_json") else response
    return payload, status


def test_success_response_with_data_and_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-001
    (data={"x": 1}, trace_id="abc12345" で payload 返却)
    対象実装: cli/lib/http_api/envelope.py::success_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(success_response(data={"x": 1}, trace_id="abc12345"))

    assert status == 200
    assert response == {"data": {"x": 1}, "trace_id": "abc12345"}


def test_success_response_with_none_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-002
    (data=None でも response 生成)
    対象実装: cli/lib/http_api/envelope.py::success_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(success_response(data=None, trace_id="trace-none"))

    assert status == 200
    assert response == {"data": None, "trace_id": "trace-none"}


def test_success_response_with_empty_trace_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-003
    (trace_id="" でも response 生成)
    対象実装: cli/lib/http_api/envelope.py::success_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(success_response(data={"ok": True}, trace_id=""))

    assert status == 200
    assert response == {"data": {"ok": True}, "trace_id": ""}


def test_success_response_with_custom_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-004
    (status=201 でそのまま返却)
    対象実装: cli/lib/http_api/envelope.py::success_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(success_response(data={"created": True}, trace_id="trace-201", status=201))

    assert status == 201
    assert response == {"data": {"created": True}, "trace_id": "trace-201"}


def test_error_response_with_bad_request_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-005
    (code="BAD_REQUEST" で 400 返却)
    対象実装: cli/lib/http_api/envelope.py::error_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(error_response("BAD_REQUEST", "x", "trace-400", 400))

    assert status == 400
    assert response == {
        "error": {"code": "BAD_REQUEST", "message": "x"},
        "trace_id": "trace-400",
    }


def test_error_response_with_not_found_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-006
    (code="NOT_FOUND" で 404 返却)
    対象実装: cli/lib/http_api/envelope.py::error_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(error_response("NOT_FOUND", "missing", "trace-404", 404))

    assert status == 404
    assert response == {
        "error": {"code": "NOT_FOUND", "message": "missing"},
        "trace_id": "trace-404",
    }


def test_error_response_with_internal_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-007
    (code="INTERNAL_ERROR" で 500 返却)
    対象実装: cli/lib/http_api/envelope.py::error_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(error_response("INTERNAL_ERROR", "boom", "trace-500", 500))

    assert status == 500
    assert response == {
        "error": {"code": "INTERNAL_ERROR", "message": "boom"},
        "trace_id": "trace-500",
    }


def test_error_response_with_blank_trace_id_and_custom_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-ENV-008
    (trace_id="" と status=418 でも payload が成立)
    対象実装: cli/lib/http_api/envelope.py::error_response
    対象設計 (①): D-API EXT §共通 Envelope schema
    """

    monkeypatch.setattr("http_api.envelope.jsonify", lambda payload: payload)
    response, status = _normalize_response(error_response("TEAPOT", "short and stout", "", 418))

    assert status == 418
    assert response == {
        "error": {"code": "TEAPOT", "message": "short and stout"},
        "trace_id": "",
    }
