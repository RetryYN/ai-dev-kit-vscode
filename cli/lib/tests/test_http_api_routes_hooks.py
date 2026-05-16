"""PLAN-074 single-unit tests for cli/lib/http_api/routes/hooks.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §3.3 hook callback endpoint
- 対象実装 (② D-IMPL): cli/lib/http_api/routes/hooks.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.7
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_routes_hooks.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from http_api.routes import hooks as hooks_routes
from http_api.server import create_app


def _headers(trace_id: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer test-token-123",
        "X-Trace-Id": trace_id,
    }


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "helix.db"
    with helix_db._write_connection(str(path)) as conn:
        helix_db.migrate(conn)
    monkeypatch.setenv("HELIX_DB_PATH", str(path))
    return path


@pytest.fixture
def client_with_token(db_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-123")
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def valid_run_id(db_path: Path) -> int:
    with helix_db._write_connection(str(db_path)) as conn:
        return helix_db.insert_automation_run(
            conn,
            trigger_source="test",
            run_kind="pretool",
        )


@pytest.mark.parametrize(
    ("hook_kind", "trace_id", "actor"),
    [
        ("pretool", "trace-hk-001", "test-pretool"),
        ("posttool", "trace-hk-002", "test-posttool"),
        ("stop", "trace-hk-003", "test-stop"),
        ("session_start", "trace-hk-004", "test-session-start"),
    ],
)
def test_hook_callback_valid_kinds_return_200(
    client_with_token,
    valid_run_id: int,
    hook_kind: str,
    trace_id: str,
    actor: str,
):
    """DoD 検証: PLAN-074-unit-test-design.md U-HK-001〜U-HK-004 (hook_kind 正常 → 200)
    対象実装: cli/lib/http_api/routes/hooks.py::hook_callback
    対象設計 (①): D-API EXT §3.3 hook callback endpoint
    """
    with patch.object(hooks_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_insert:
        response = client_with_token.post(
            f"/api/v1/automation/hooks/{hook_kind}/callback",
            json={
                "hook_kind": hook_kind,
                "run_id": valid_run_id,
                "actor": actor,
            },
            headers=_headers(trace_id),
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["acknowledged"] is True
    assert "persisted_at" in body["data"]
    mock_insert.assert_called_once()
    kwargs = mock_insert.call_args.kwargs
    assert kwargs["audit_kind"] == "hook_exec"
    assert kwargs["actor"] == actor
    assert kwargs["run_id"] == valid_run_id
    assert kwargs["payload"] == {"hook_kind": hook_kind}


def test_hook_callback_invalid_kind_returns_400(client_with_token, valid_run_id: int):
    """DoD 検証: PLAN-074-unit-test-design.md U-HK-005 (hook_kind=invalid → 400)
    対象実装: cli/lib/http_api/routes/hooks.py::hook_callback
    対象設計 (①): D-API EXT §3.3 hook callback endpoint
    """
    with patch.object(hooks_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_insert:
        response = client_with_token.post(
            "/api/v1/automation/hooks/invalid/callback",
            json={
                "hook_kind": "invalid",
                "run_id": valid_run_id,
                "actor": "test-invalid",
            },
            headers=_headers("trace-hk-005"),
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )

    assert response.status_code == 400
    mock_insert.assert_not_called()


def test_hook_callback_kind_mismatch_returns_400(client_with_token, valid_run_id: int):
    """DoD 検証: PLAN-074-unit-test-design.md U-HK-006 (path と body の hook_kind 不一致 → 400)
    対象実装: cli/lib/http_api/routes/hooks.py::hook_callback
    対象設計 (①): D-API EXT §3.3 hook callback endpoint
    """
    with patch.object(hooks_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_insert:
        response = client_with_token.post(
            "/api/v1/automation/hooks/pretool/callback",
            json={
                "hook_kind": "posttool",
                "run_id": valid_run_id,
                "actor": "test-mismatch",
            },
            headers=_headers("trace-hk-006"),
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )

    assert response.status_code == 400
    mock_insert.assert_not_called()
