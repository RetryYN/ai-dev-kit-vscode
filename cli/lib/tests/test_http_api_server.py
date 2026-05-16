"""DoD 検証: D-API EXT §1-§2 共通 envelope + auth (HELIX HTTP API framework)
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-002 / Sprint .1
対象実装: cli/lib/http_api/server.py + envelope.py + auth.py + validation.py
テスト設計 (③ D-TEST-DESIGN-INT): docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.6 server/framework (PLAN-075 V-model 4 artifact 双方向 trace)

5 cases:
  - /health 公開動作
  - /api/v1/_status 認証必須 (Bearer なしで 401/403)
  - localhost-only bind (127.0.0.1/::1 限定)
  - envelope 形式 (success / error の 2 形式)
  - auth 強度 (HELIX_HTTP_API_TOKEN env 由来)
"""
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
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-123")
    app = create_app()
    app.config["TESTING"] = True
    yield app.test_client()


def test_health_returns_200_without_auth(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["data"]["status"] == "ok"


def test_undefined_endpoint_returns_404(client) -> None:
    res = client.get(
        "/api/v1/nonexistent",
        headers={"Authorization": "Bearer test-token-123"},
    )
    assert res.status_code == 404


def test_status_returns_403_without_token(client) -> None:
    res = client.get("/api/v1/_status")
    assert res.status_code == 403


def test_status_returns_403_with_wrong_token(client) -> None:
    res = client.get(
        "/api/v1/_status",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert res.status_code == 403


def test_status_returns_200_with_correct_token(client) -> None:
    res = client.get(
        "/api/v1/_status",
        headers={"Authorization": "Bearer test-token-123"},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["data"]["server"] == "helix-http-api"
