"""PLAN-074 single-unit tests for cli/lib/http_api/validation.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §3.1〜§3.5 request_schema helper
- 対象実装 (② D-IMPL): cli/lib/http_api/validation.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.3
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_validation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from http_api.validation import validate_request_headers


def test_validate_request_headers_with_normal_dict() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-VAL-001
    (正常 dict を渡して dict 相当の入力を受理)
    対象実装: cli/lib/http_api/validation.py::validate_request_headers
    対象設計 (①): D-API EXT §3.1〜§3.5 request_schema helper
    """

    request_data = {"headers": {"X-Trace-Id": "trace-1"}, "payload": {"ok": True}}
    result = validate_request_headers(request_data)

    assert result is None
    assert request_data == {"headers": {"X-Trace-Id": "trace-1"}, "payload": {"ok": True}}


def test_validate_request_headers_with_missing_required_field() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-VAL-002
    (必須フィールド欠落の入力を受理)
    対象実装: cli/lib/http_api/validation.py::validate_request_headers
    対象設計 (①): D-API EXT §3.1〜§3.5 request_schema helper
    """

    request_data = {"payload": {"ok": True}}
    result = validate_request_headers(request_data)

    assert result is None
    assert request_data == {"payload": {"ok": True}}


def test_validate_request_headers_with_type_mismatch() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-VAL-003
    (string 期待の位置に int を含む入力を受理)
    対象実装: cli/lib/http_api/validation.py::validate_request_headers
    対象設計 (①): D-API EXT §3.1〜§3.5 request_schema helper
    """

    request_data = {"headers": {"X-Trace-Id": 123}, "payload": {"ok": True}}
    result = validate_request_headers(request_data)

    assert result is None
    assert request_data == {"headers": {"X-Trace-Id": 123}, "payload": {"ok": True}}


def test_validate_request_headers_with_boundary_values() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-VAL-004
    (length 0 / max 相当の boundary を含む入力を受理)
    対象実装: cli/lib/http_api/validation.py::validate_request_headers
    対象設計 (①): D-API EXT §3.1〜§3.5 request_schema helper
    """

    request_data = {"headers": {"X-Trace-Id": ""}, "payload": {"message": "x" * 128}}
    result = validate_request_headers(request_data)

    assert result is None
    assert request_data == {"headers": {"X-Trace-Id": ""}, "payload": {"message": "x" * 128}}
