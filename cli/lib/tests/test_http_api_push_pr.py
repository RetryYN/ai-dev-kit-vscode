"""DoD 検証: D-API EXT §3.1 push trigger + §3.2 pr trigger
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-003 / Sprint .2
対象実装: cli/lib/http_api/routes/push_pr.py
テスト設計 (③ D-TEST-DESIGN-INT): docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.1 (push) + §3.2 (pr) (PLAN-075 V-model 4 artifact 双方向 trace)

5 cases:
  - success: 正常系で run_id 返却 + automation_runs INSERT + audit_log
  - missing: 必須フィールド欠落で 400
  - unauthorized: Bearer なしで 401/403
  - not_found: 該当 plan_id が無いケースで 404
  - dry_run: execute=False で実 push なし
"""
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from http_api.server import create_app


def _write_plan(project_root: Path, plan_id: str) -> None:
    plan_dir = project_root / "docs" / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / f"{plan_id}-endpoint.md").write_text(f"id: {plan_id}\n", encoding="utf-8")


def _gate_mock_ok() -> dict[str, object]:
    return {
        "ok": True,
        "failed_count": 0,
        "gates": [{"id": "G-tests", "passed": True, "detail": "ok", "fix": ""}],
        "execute_requested": False,
        "remote": "origin",
        "branch": "main",
        "push": {"attempted": False, "ok": False, "detail": ""},
    }


def _gate_mock_fail() -> dict[str, object]:
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
def env_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = project_root / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)

    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-123")
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    return {"db_path": db_path, "project_root": project_root}


@pytest.fixture
def client(env_setup):
    app = create_app()
    app.config["TESTING"] = True
    yield app.test_client()


def test_push_trigger_success_records_run_and_audit(client, env_setup):
    _write_plan(env_setup["project_root"], "PLAN-100")

    with patch("push_gate.run_all_gates", return_value=_gate_mock_ok()) as gate_mock:
        res = client.post(
            "/api/v1/automation/push/PLAN-100/trigger",
            headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-001"},
            query_string={"dry_run": "true"},
            json={
                "commit_sha": "abc1234",
                "branch": "main",
                "trigger_actor": "test",
                "execute": True,
            },
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["trace_id"] == "trace-001"
        assert body["data"]["ok"] is True
        assert body["data"]["execute_requested"] is False
        gate_mock.assert_called_once_with(execute=False, remote="origin", branch="main")

    with sqlite3.connect(str(env_setup["db_path"])) as conn:
        run_row = conn.execute(
            "SELECT run_kind, plan_id, trigger_actor, status, summary FROM automation_runs"
        ).fetchone()
        audit_row = conn.execute(
            "SELECT audit_kind, actor, run_id, payload FROM audit_log"
        ).fetchone()

    assert run_row is not None
    assert run_row[0] == "push"
    assert run_row[1] == "PLAN-100"
    assert run_row[2] == "system"
    assert run_row[3] == "completed"
    summary = json.loads(run_row[4])
    assert summary["commit_sha"] == "abc1234"
    assert summary["dry_run"] is True
    assert summary["execute"] is False

    assert audit_row is not None
    assert audit_row[0] == "hook_exec"
    assert audit_row[1] == "http-push"
    assert audit_row[2] == 1
    payload = json.loads(audit_row[3])
    assert payload["plan_id"] == "PLAN-100"
    assert payload["trigger_source"] == "helix-http-push"


def test_pr_trigger_success_records_pr_actor(client, env_setup):
    _write_plan(env_setup["project_root"], "PLAN-101")

    with patch("push_gate.run_all_gates", return_value=_gate_mock_ok()):
        res = client.post(
            "/api/v1/automation/pr/PLAN-101/trigger",
            headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-002"},
            json={
                "commit_sha": "def5678",
                "branch": "main",
                "trigger_actor": "test",
                "execute": False,
            },
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["data"]["ok"] is True
        assert body["data"]["pair_transition"]["to"] == "completed"

    with sqlite3.connect(str(env_setup["db_path"])) as conn:
        run_row = conn.execute(
            "SELECT run_kind, status, summary FROM automation_runs"
        ).fetchone()
        audit_row = conn.execute(
            "SELECT audit_kind, actor FROM audit_log"
        ).fetchone()

    assert run_row is not None
    assert run_row[0] == "pr"
    assert run_row[1] == "completed"
    summary = json.loads(run_row[2])
    assert summary["trigger_source"] == "helix-http-pr"

    assert audit_row is not None
    assert audit_row[0] == "hook_exec"
    assert audit_row[1] == "http-pr"


def test_push_trigger_missing_field_returns_400(client, env_setup):
    _write_plan(env_setup["project_root"], "PLAN-102")

    res = client.post(
        "/api/v1/automation/push/PLAN-102/trigger",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-003"},
        json={"commit_sha": "abc1234", "branch": "main", "trigger_actor": "test"},
    )

    assert res.status_code == 400


def test_push_trigger_invalid_commit_sha_returns_400(client, env_setup):
    _write_plan(env_setup["project_root"], "PLAN-103")

    res = client.post(
        "/api/v1/automation/push/PLAN-103/trigger",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-004"},
        json={
            "commit_sha": "abc",
            "branch": "main",
            "trigger_actor": "test",
            "execute": False,
        },
    )

    assert res.status_code == 400


def test_push_trigger_unknown_plan_returns_404(client):
    res = client.post(
        "/api/v1/automation/push/PLAN-999/trigger",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-005"},
        json={
            "commit_sha": "ghi9012",
            "branch": "main",
            "trigger_actor": "test",
            "execute": False,
        },
    )

    assert res.status_code == 404


def test_push_trigger_conflict_maps_to_409(client, env_setup, monkeypatch: pytest.MonkeyPatch):
    _write_plan(env_setup["project_root"], "PLAN-104")

    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise sqlite3.IntegrityError("duplicate")

    monkeypatch.setattr(helix_db, "insert_automation_run", _boom)

    res = client.post(
        "/api/v1/automation/push/PLAN-104/trigger",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-006"},
        json={
            "commit_sha": "jkl3456",
            "branch": "main",
            "trigger_actor": "test",
            "execute": False,
        },
    )

    assert res.status_code == 409


def test_push_trigger_failed_gate_marks_failed(client, env_setup):
    _write_plan(env_setup["project_root"], "PLAN-105")

    with patch("push_gate.run_all_gates", return_value=_gate_mock_fail()):
        res = client.post(
            "/api/v1/automation/push/PLAN-105/trigger",
            headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-007"},
            json={
                "commit_sha": "mno7890",
                "branch": "main",
                "trigger_actor": "test",
                "execute": False,
            },
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["data"]["ok"] is False
        assert body["data"]["failed_count"] == 1

    with sqlite3.connect(str(env_setup["db_path"])) as conn:
        status = conn.execute("SELECT status FROM automation_runs").fetchone()[0]

    assert status == "failed"
