"""PLAN-074 single-unit tests for cli/lib/http_api/routes/push_pr.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §3.1 push trigger endpoint + §3.2 pr trigger endpoint
- 対象実装 (② D-IMPL): cli/lib/http_api/routes/push_pr.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.8
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_routes_push_pr.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from http_api.routes import push_pr as push_pr_routes
from http_api.server import create_app


def _headers(trace_id: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer test-token-123",
        "X-Trace-Id": trace_id,
    }


def _write_plan(project_root: Path, plan_id: str) -> None:
    plan_dir = project_root / "docs" / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / f"{plan_id}-endpoint.md").write_text(f"id: {plan_id}\n", encoding="utf-8")


def _gate_pass_result() -> dict[str, object]:
    return {
        "ok": True,
        "failed_count": 0,
        "gates": [{"id": "G-tests", "passed": True, "detail": "ok", "fix": ""}],
        "execute_requested": False,
        "remote": "origin",
        "branch": "main",
        "push": {"attempted": False, "ok": False, "detail": ""},
    }


def _gate_fail_result() -> dict[str, object]:
    return {
        "ok": False,
        "failed_count": 1,
        "gates": [{"id": "G-tests", "passed": False, "detail": "fail", "fix": "fix-it"}],
        "execute_requested": False,
        "remote": "origin",
        "branch": "main",
        "push": {"attempted": False, "ok": False, "detail": ""},
    }


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "project"
    root.mkdir()
    db_path = root / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)

    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-123")
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))
    return {"root": root, "db_path": db_path}


@pytest.fixture
def app_with_token(project_root):
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client_with_token(app_with_token):
    return app_with_token.test_client()
    return app.test_client()


def test_push_trigger_gate_pass_returns_run_id(client_with_token, project_root):
    """DoD 検証: PLAN-074-unit-test-design.md U-PUSH-001 (execute=False, gate PASS → 200 + run_id)
    対象実装: cli/lib/http_api/routes/push_pr.py::push_trigger
    対象設計 (①): D-API EXT §3.1 push trigger endpoint
    """
    plan_id = "PLAN-075-PUSH-001"
    _write_plan(project_root["root"], plan_id)

    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock(return_value=_gate_pass_result())) as mock_gate:
        with patch.object(push_pr_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_audit:
            response = client_with_token.post(
                f"/api/v1/automation/push/{plan_id}/trigger",
                json={
                    "commit_sha": "abc1234",
                    "branch": "main",
                    "trigger_actor": "test-actor",
                    "execute": False,
                },
                headers=_headers("trace-push-001"),
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["run_id"] == 1
    assert body["data"]["ok"] is True
    assert body["data"]["failed_count"] == 0
    assert body["data"]["pair_transition"]["to"] == "completed"
    mock_gate.assert_called_once_with(execute=False, remote="origin", branch="main")
    mock_audit.assert_called_once()

    with helix_db._write_connection(str(project_root["db_path"])) as conn:
        row = conn.execute(
            "SELECT run_kind, status, summary FROM automation_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row[0] == "push"
    assert row[1] == "completed"
    summary = json.loads(row[2])
    assert summary["trigger_source"] == "helix-http-push"
    assert summary["execute"] is False


def test_push_trigger_gate_fail_returns_failed_run(client_with_token, project_root):
    """DoD 検証: PLAN-074-unit-test-design.md U-PUSH-002 (execute=False, gate FAIL → 200 + failed gate)
    対象実装: cli/lib/http_api/routes/push_pr.py::push_trigger
    対象設計 (①): D-API EXT §3.1 push trigger endpoint
    """
    plan_id = "PLAN-075-PUSH-002"
    _write_plan(project_root["root"], plan_id)

    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock(return_value=_gate_fail_result())) as mock_gate:
        with patch.object(push_pr_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_audit:
            response = client_with_token.post(
                f"/api/v1/automation/push/{plan_id}/trigger",
                json={
                    "commit_sha": "def5678",
                    "branch": "main",
                    "trigger_actor": "test-actor",
                    "execute": False,
                },
                headers=_headers("trace-push-002"),
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["ok"] is False
    assert body["data"]["failed_count"] == 1
    assert body["data"]["pair_transition"]["to"] == "failed"
    mock_gate.assert_called_once_with(execute=False, remote="origin", branch="main")
    mock_audit.assert_called_once()

    with helix_db._write_connection(str(project_root["db_path"])) as conn:
        row = conn.execute(
            "SELECT run_kind, status, summary FROM automation_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row[0] == "push"
    assert row[1] == "failed"
    summary = json.loads(row[2])
    assert summary["trigger_source"] == "helix-http-push"
    assert summary["execute"] is False


def test_push_trigger_missing_fields_return_400(client_with_token, project_root):
    """DoD 検証: PLAN-074-unit-test-design.md U-PUSH-003 (必須欠落 → 400)
    対象実装: cli/lib/http_api/routes/push_pr.py::push_trigger
    対象設計 (①): D-API EXT §3.1 push trigger endpoint
    """
    plan_id = "PLAN-075-PUSH-003"
    _write_plan(project_root["root"], plan_id)

    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock()) as mock_gate:
        response = client_with_token.post(
            f"/api/v1/automation/push/{plan_id}/trigger",
            json={
                "commit_sha": "abc1234",
                "branch": "main",
                "trigger_actor": "test-actor",
            },
            headers=_headers("trace-push-003"),
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )

    assert response.status_code == 400
    mock_gate.assert_not_called()


def test_push_trigger_empty_plan_id_returns_400(app_with_token):
    """DoD 検証: PLAN-074-unit-test-design.md U-PUSH-004 (plan_id 不正 (空) → 400)
    対象実装: cli/lib/http_api/routes/push_pr.py::push_trigger
    対象設計 (①): D-API EXT §3.1 push trigger endpoint
    """
    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock()) as mock_gate:
        request_mock = MagicMock()
        request_mock.headers = _headers("trace-push-004")
        request_mock.args = {}
        request_mock.get_json.return_value = {
            "commit_sha": "abc1234",
            "branch": "main",
            "trigger_actor": "test-actor",
            "execute": False,
        }
        with patch.object(push_pr_routes, "request", request_mock):
            response = push_pr_routes.push_trigger("")

    assert response.status_code == 400
    mock_gate.assert_not_called()


def test_pr_trigger_gate_pass_returns_run_id(client_with_token, project_root):
    """DoD 検証: PLAN-074-unit-test-design.md U-PR-001 (execute=False, gate PASS → 200 + run_id)
    対象実装: cli/lib/http_api/routes/push_pr.py::pr_trigger
    対象設計 (①): D-API EXT §3.2 pr trigger endpoint
    """
    plan_id = "PLAN-075-PR-001"
    _write_plan(project_root["root"], plan_id)

    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock(return_value=_gate_pass_result())) as mock_gate:
        with patch.object(push_pr_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_audit:
            response = client_with_token.post(
                f"/api/v1/automation/pr/{plan_id}/trigger",
                json={
                    "commit_sha": "ghi9012",
                    "branch": "main",
                    "trigger_actor": "test-actor",
                    "execute": False,
                },
                headers=_headers("trace-pr-001"),
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["run_id"] == 1
    assert body["data"]["ok"] is True
    assert body["data"]["pair_transition"]["to"] == "completed"
    mock_gate.assert_called_once_with(execute=False, remote="origin", branch="main")
    mock_audit.assert_called_once()

    with helix_db._write_connection(str(project_root["db_path"])) as conn:
        row = conn.execute(
            "SELECT run_kind, status, summary FROM automation_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row[0] == "pr"
    assert row[1] == "completed"
    summary = json.loads(row[2])
    assert summary["trigger_source"] == "helix-http-pr"
    assert summary["execute"] is False


def test_pr_trigger_gate_fail_returns_failed_run(client_with_token, project_root):
    """DoD 検証: PLAN-074-unit-test-design.md U-PR-002 (execute=False, gate FAIL → 200 + failed gate)
    対象実装: cli/lib/http_api/routes/push_pr.py::pr_trigger
    対象設計 (①): D-API EXT §3.2 pr trigger endpoint
    """
    plan_id = "PLAN-075-PR-002"
    _write_plan(project_root["root"], plan_id)

    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock(return_value=_gate_fail_result())) as mock_gate:
        with patch.object(push_pr_routes.helix_db, "insert_audit_log", new=MagicMock()) as mock_audit:
            response = client_with_token.post(
                f"/api/v1/automation/pr/{plan_id}/trigger",
                json={
                    "commit_sha": "jkl3456",
                    "branch": "main",
                    "trigger_actor": "test-actor",
                    "execute": False,
                },
                headers=_headers("trace-pr-002"),
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["ok"] is False
    assert body["data"]["failed_count"] == 1
    assert body["data"]["pair_transition"]["to"] == "failed"
    mock_gate.assert_called_once_with(execute=False, remote="origin", branch="main")
    mock_audit.assert_called_once()

    with helix_db._write_connection(str(project_root["db_path"])) as conn:
        row = conn.execute(
            "SELECT run_kind, status, summary FROM automation_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row[0] == "pr"
    assert row[1] == "failed"
    summary = json.loads(row[2])
    assert summary["trigger_source"] == "helix-http-pr"
    assert summary["execute"] is False


def test_pr_trigger_missing_fields_return_400(client_with_token, project_root):
    """DoD 検証: PLAN-074-unit-test-design.md U-PR-003 (必須欠落 → 400)
    対象実装: cli/lib/http_api/routes/push_pr.py::pr_trigger
    対象設計 (①): D-API EXT §3.2 pr trigger endpoint
    """
    plan_id = "PLAN-075-PR-003"
    _write_plan(project_root["root"], plan_id)

    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock()) as mock_gate:
        response = client_with_token.post(
            f"/api/v1/automation/pr/{plan_id}/trigger",
            json={
                "commit_sha": "ghi9012",
                "branch": "main",
                "trigger_actor": "test-actor",
            },
            headers=_headers("trace-pr-003"),
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )

    assert response.status_code == 400
    mock_gate.assert_not_called()


def test_pr_trigger_empty_plan_id_returns_400(app_with_token):
    """DoD 検証: PLAN-074-unit-test-design.md U-PR-004 (plan_id 不正 → 400)
    対象実装: cli/lib/http_api/routes/push_pr.py::pr_trigger
    対象設計 (①): D-API EXT §3.2 pr trigger endpoint
    """
    with patch.object(push_pr_routes.push_gate, "run_all_gates", new=MagicMock()) as mock_gate:
        request_mock = MagicMock()
        request_mock.headers = _headers("trace-pr-004")
        request_mock.args = {}
        request_mock.get_json.return_value = {
            "commit_sha": "ghi9012",
            "branch": "main",
            "trigger_actor": "test-actor",
            "execute": False,
        }
        with patch.object(push_pr_routes, "request", request_mock):
            response = push_pr_routes.pr_trigger("")

    assert response.status_code == 400
    mock_gate.assert_not_called()
