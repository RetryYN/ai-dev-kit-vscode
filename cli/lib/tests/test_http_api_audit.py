"""DoD 検証: D-API EXT §3.4 audit endpoint
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-005 / Sprint .4
対象実装: cli/lib/http_api/routes/audit.py
テスト設計 (③ D-TEST-DESIGN-INT): docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.4 audit endpoint (PLAN-075 V-model 4 artifact 双方向 trace)

5 cases:
  - success: HTTP audit_kind を payload.http_audit_kind に退避、helix_db には endpoint_call
  - missing 必須フィールドで 400
  - invalid audit_kind (helix_db 内部 enum を HTTP では拒否) で 400
  - run_id 未存在で 404
  - unauthorized で 401/403
"""
from __future__ import annotations

import json
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
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-abc")
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    return db_path, run_id


@pytest.fixture
def client(env_setup):
    app = create_app()
    app.config["TESTING"] = True
    yield app.test_client()


def _audit_body(run_id: int, audit_kind: str = "footer", **extra):
    body = {
        "audit_kind": audit_kind,
        "payload": {"summary": "test"},
        "run_id": run_id,
        "actor": "cli",
    }
    body.update(extra)
    return body


def test_audit_log_success(client, env_setup):
    db_path, run_id = env_setup
    body = _audit_body(run_id, audit_kind="footer", related_plan_id="PLAN-074")
    res = client.post(
        "/api/v1/automation/audit/log",
        headers={
            "Authorization": "Bearer test-token-abc",
            "X-Trace-Id": "trace-aud-1",
            "Content-Type": "application/json",
        },
        json=body,
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["data"]["acknowledged"] is True
    assert "persisted_at" in data["data"]

    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            "SELECT audit_kind, actor, run_id, payload FROM audit_log WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    assert row is not None
    assert row[0] == "endpoint_call"
    assert row[1] == "cli"
    payload_db = json.loads(row[3])
    assert payload_db["http_audit_kind"] == "footer"
    assert payload_db["related_plan_id"] == "PLAN-074"


def test_audit_log_missing_fields(client):
    res = client.post(
        "/api/v1/automation/audit/log",
        headers={
            "Authorization": "Bearer test-token-abc",
            "X-Trace-Id": "trace-aud-2",
            "Content-Type": "application/json",
        },
        json={"audit_kind": "footer"},
    )
    assert res.status_code == 400


def test_audit_log_invalid_audit_kind(client, env_setup):
    _, run_id = env_setup
    body = _audit_body(run_id, audit_kind="hook_exec")
    res = client.post(
        "/api/v1/automation/audit/log",
        headers={
            "Authorization": "Bearer test-token-abc",
            "X-Trace-Id": "trace-aud-3",
            "Content-Type": "application/json",
        },
        json=body,
    )
    assert res.status_code == 400


def test_audit_log_run_id_not_found(client, env_setup):
    _, _ = env_setup
    body = _audit_body(99999, audit_kind="summary")
    res = client.post(
        "/api/v1/automation/audit/log",
        headers={
            "Authorization": "Bearer test-token-abc",
            "X-Trace-Id": "trace-aud-4",
            "Content-Type": "application/json",
        },
        json=body,
    )
    assert res.status_code == 404


def test_audit_log_unauthorized(client, env_setup):
    _, run_id = env_setup
    body = _audit_body(run_id)
    res = client.post(
        "/api/v1/automation/audit/log",
        headers={
            "X-Trace-Id": "trace-aud-5",
            "Content-Type": "application/json",
        },
        json=body,
    )
    assert res.status_code in (401, 403)
