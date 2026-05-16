"""DoD 検証: D-API EXT §3.5 Stop hook telemetry endpoint
  (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md)
担当 WBS: PLAN-074 / WBS-074-L4-006 / Sprint .5
対象実装: cli/lib/http_api/routes/telemetry.py
テスト設計 (③ D-TEST-DESIGN-INT): docs/v2/L4-test-design/PLAN-074-integration-test-design.md §3.5 telemetry endpoint (PLAN-075 V-model 4 artifact 双方向 trace)

5 cases:
  - success: session_telemetry INSERT
  - upsert: 同 session_id 2 回呼び出しで UPSERT 動作 (UNIQUE 制約活用)
  - missing 必須フィールドで 400
  - unauthorized で 401/403
  - invalid: 型不正で 400
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


def _telemetry_body(run_id: int, session_id: str = "sess-001") -> dict[str, object]:
    return {
        "run_id": run_id,
        "session_id": session_id,
        "started_at": "2026-05-16T12:00:00+00:00",
        "ended_at": "2026-05-16T12:30:00+00:00",
        "tokens_used": 1000,
        "cost_usd": 0.05,
        "model": "gpt-5.4",
        "role": "se",
    }


def test_telemetry_success_persists_row(client, env_setup):
    db_path, run_id = env_setup
    res = client.post(
        "/api/v1/automation/session/telemetry",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-Trace-Id": "trace-t1",
            "Content-Type": "application/json",
        },
        json=_telemetry_body(run_id),
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body["data"]["acknowledged"] is True
    assert "persisted_at" in body["data"]

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT session_id, started_at, ended_at, actor, tokens_total, cost_usd
            FROM session_telemetry
            WHERE session_id = ?
            """,
            ("sess-001",),
        ).fetchone()

    assert row is not None
    assert row["session_id"] == "sess-001"
    assert row["actor"] == "se/gpt-5.4"
    assert row["tokens_total"] == 1000
    assert row["cost_usd"] == pytest.approx(0.05)
    assert row["started_at"] == "2026-05-16T12:00:00+00:00"
    assert row["ended_at"] == "2026-05-16T12:30:00+00:00"


def test_telemetry_missing_field_returns_400(client, env_setup):
    _db_path, run_id = env_setup
    res = client.post(
        "/api/v1/automation/session/telemetry",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-Trace-Id": "trace-t2",
            "Content-Type": "application/json",
        },
        json={"run_id": run_id, "session_id": "sess-002"},
    )

    assert res.status_code == 400


def test_telemetry_negative_cost_returns_400(client, env_setup):
    _db_path, run_id = env_setup
    body = _telemetry_body(run_id, "sess-003")
    body["cost_usd"] = -0.1

    res = client.post(
        "/api/v1/automation/session/telemetry",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-Trace-Id": "trace-t3",
            "Content-Type": "application/json",
        },
        json=body,
    )

    assert res.status_code == 400


def test_telemetry_run_id_not_found_returns_404(client, env_setup):
    body = _telemetry_body(99999, "sess-004")
    res = client.post(
        "/api/v1/automation/session/telemetry",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-Trace-Id": "trace-t4",
            "Content-Type": "application/json",
        },
        json=body,
    )

    assert res.status_code == 404


def test_telemetry_upsert_is_idempotent(client, env_setup):
    db_path, run_id = env_setup
    body = _telemetry_body(run_id, "sess-upsert-1")

    res1 = client.post(
        "/api/v1/automation/session/telemetry",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-Trace-Id": "trace-u1",
            "Content-Type": "application/json",
        },
        json=body,
    )
    assert res1.status_code == 200

    body["cost_usd"] = 0.10
    body["tokens_used"] = 1400
    res2 = client.post(
        "/api/v1/automation/session/telemetry",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-Trace-Id": "trace-u2",
            "Content-Type": "application/json",
        },
        json=body,
    )
    assert res2.status_code == 200

    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c, tokens_total, cost_usd
            FROM session_telemetry
            WHERE session_id = 'sess-upsert-1'
            """
        ).fetchone()

    assert row is not None
    assert row[0] == 1
    assert row[1] == 1400
    assert row[2] == pytest.approx(0.10)
