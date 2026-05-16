"""DoD 検証: D-API EXT §3.3 hook callback
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-004 / Sprint .3
対象実装: cli/lib/http_api/routes/hooks.py
テスト設計 (③ D-TEST-DESIGN-INT): docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.3 hook callback (PLAN-075 V-model 4 artifact 双方向 trace)

5 cases:
  - 各 hook_kind (pretool / posttool / stop / session_start) で正常系
  - invalid hook_kind で 400
  - missing 必須フィールドで 400
"""
import sqlite3
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from http_api.server import create_app


@pytest.fixture
def env_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "helix.db"
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)
        run_id = helix_db.insert_automation_run(conn, trigger_source="test", run_kind="push")
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-123")
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    return db_path, run_id


@pytest.fixture
def client(env_setup):
    app = create_app()
    app.config["TESTING"] = True
    yield app.test_client()


def test_hook_callback_pretool_success(client, env_setup):
    _db_path, run_id = env_setup
    res = client.post(
        "/api/v1/automation/hooks/pretool/callback",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-h1"},
        json={
            "hook_kind": "pretool",
            "run_id": run_id,
            "actor": "test",
            "payload": {"tool": "ask-user"},
        },
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["trace_id"] == "trace-h1"
    assert body["data"]["acknowledged"] is True
    assert "persisted_at" in body["data"]


def test_hook_callback_invalid_kind(client, env_setup):
    _db_path, run_id = env_setup
    res = client.post(
        "/api/v1/automation/hooks/invalid_kind/callback",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-h2"},
        json={"hook_kind": "invalid_kind", "run_id": run_id},
    )
    assert res.status_code == 400


def test_hook_callback_kind_mismatch(client, env_setup):
    _db_path, run_id = env_setup
    res = client.post(
        "/api/v1/automation/hooks/pretool/callback",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-h3"},
        json={"hook_kind": "posttool", "run_id": run_id},
    )
    assert res.status_code == 400


def test_hook_callback_run_id_not_found(client):
    res = client.post(
        "/api/v1/automation/hooks/stop/callback",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-h4"},
        json={"hook_kind": "stop", "run_id": 99999},
    )
    assert res.status_code == 404


def test_hook_callback_writes_audit_log(client, env_setup):
    db_path, run_id = env_setup
    res = client.post(
        "/api/v1/automation/hooks/session_start/callback",
        headers={"Authorization": "Bearer test-token-123", "X-Trace-Id": "trace-h5"},
        json={"hook_kind": "session_start", "run_id": run_id, "actor": "http-test"},
    )
    assert res.status_code == 200

    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            "SELECT actor, run_id FROM audit_log WHERE actor = 'http-test'"
        ).fetchone()
    assert row is not None
    assert row[1] == run_id
