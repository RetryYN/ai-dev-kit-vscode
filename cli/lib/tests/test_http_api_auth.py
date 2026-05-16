"""PLAN-074 single-unit tests for cli/lib/http_api/auth.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §3.1〜§3.5 共通 framework 層
- 対象実装 (② D-IMPL): cli/lib/http_api/auth.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.1
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_auth.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from http_api.auth import require_localhost_and_bearer


def _call_require_localhost_and_bearer(
    *,
    remote_addr: str,
    bearer: str | None,
    env_token: str | None,
):
    headers = {}
    if bearer is not None:
        headers["Authorization"] = f"Bearer {bearer}"

    env_patch = {}
    if env_token is not None:
        env_patch["HELIX_HTTP_API_TOKEN"] = env_token

    fake_request = SimpleNamespace(headers=headers, remote_addr=remote_addr)

    with patch.dict(os.environ, env_patch, clear=False), patch(
        "http_api.auth.request",
        fake_request,
    ):
        result = require_localhost_and_bearer()
        if result is None:
            return None
        if isinstance(result, tuple):
            return result
        return result, getattr(result, "status_code", None)


def test_require_localhost_and_bearer_localhost_v4_valid_token() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-AUTH-001
    (remote_addr=127.0.0.1, Bearer=valid で pass through)
    対象実装: cli/lib/http_api/auth.py::require_localhost_and_bearer
    対象設計 (①): D-API EXT §3.1〜§3.5 共通 framework 層
    """

    result = _call_require_localhost_and_bearer(
        remote_addr="127.0.0.1",
        bearer="test-token",
        env_token="test-token",
    )

    assert result is None


def test_require_localhost_and_bearer_localhost_v6_valid_token() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-AUTH-002
    (remote_addr=::1, Bearer=valid で pass through)
    対象実装: cli/lib/http_api/auth.py::require_localhost_and_bearer
    対象設計 (①): D-API EXT §3.1〜§3.5 共通 framework 層
    """

    result = _call_require_localhost_and_bearer(
        remote_addr="::1",
        bearer="test-token",
        env_token="test-token",
    )

    assert result is None


def test_require_localhost_and_bearer_rejects_non_localhost_peer() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-AUTH-003
    (remote_addr=192.168.1.1 で 403 返却)
    対象実装: cli/lib/http_api/auth.py::require_localhost_and_bearer
    対象設計 (①): D-API EXT §3.1〜§3.5 共通 framework 層
    """

    response, status = _call_require_localhost_and_bearer(
        remote_addr="192.168.1.1",
        bearer="test-token",
        env_token="test-token",
    )

    assert status == 403
    assert response.get_json()["error"]["code"] == "AUTH_FAILED"


def test_require_localhost_and_bearer_rejects_missing_authorization_header() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-AUTH-004
    (remote_addr=127.0.0.1, Bearer なしで 403 返却)
    対象実装: cli/lib/http_api/auth.py::require_localhost_and_bearer
    対象設計 (①): D-API EXT §3.1〜§3.5 共通 framework 層
    """

    response, status = _call_require_localhost_and_bearer(
        remote_addr="127.0.0.1",
        bearer=None,
        env_token="test-token",
    )

    assert status == 403
    assert response.get_json()["error"]["code"] == "AUTH_FAILED"


def test_require_localhost_and_bearer_rejects_invalid_token() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-AUTH-005
    (remote_addr=127.0.0.1, Bearer=invalid_token で 403 返却)
    対象実装: cli/lib/http_api/auth.py::require_localhost_and_bearer
    対象設計 (①): D-API EXT §3.1〜§3.5 共通 framework 層
    """

    response, status = _call_require_localhost_and_bearer(
        remote_addr="127.0.0.1",
        bearer="invalid_token",
        env_token="test-token",
    )

    assert status == 403
    assert response.get_json()["error"]["code"] == "AUTH_FAILED"


def test_require_localhost_and_bearer_rejects_unset_env_token() -> None:
    """DoD 検証: PLAN-074-unit-test-design.md U-AUTH-006
    (HELIX_HTTP_API_TOKEN env 未設定で config error)
    対象実装: cli/lib/http_api/auth.py::require_localhost_and_bearer
    対象設計 (①): D-API EXT §3.1〜§3.5 共通 framework 層
    """

    response, status = _call_require_localhost_and_bearer(
        remote_addr="127.0.0.1",
        bearer="test-token",
        env_token=None,
    )

    assert status == 403
    assert response.get_json()["error"]["code"] == "AUTH_NOT_CONFIGURED"
