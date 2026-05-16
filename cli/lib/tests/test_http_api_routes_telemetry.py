"""PLAN-074 single-unit tests for cli/lib/http_api/routes/telemetry.py.

V-model 4 artifact 双方向 trace (PLAN-075):
- 対象設計 (① D-API): D-API EXT §3.5 Stop hook telemetry endpoint
- 対象実装 (② D-IMPL): cli/lib/http_api/routes/telemetry.py
- テスト設計 (③ D-TEST-DESIGN-UNIT): docs/v2/L4-test-design/PLAN-074-unit-test-design.md §2.6
- 本ファイル (④ D-TEST-CODE-UNIT): cli/lib/tests/test_http_api_routes_telemetry.py
"""

from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from http_api.routes import telemetry as telemetry_module
from http_api.server import create_app


@contextmanager
def _managed_connection(conn):
    yield conn


def _auth_headers(trace_id: str = "trace-telemetry-001") -> dict[str, str]:
    return {
        "Authorization": "Bearer test-token-abc",
        "X-Trace-Id": trace_id,
    }


def _telemetry_body(
    run_id: int,
    *,
    session_id: str = "sess-001",
    started_at: str = "2026-05-17T00:00:00Z",
    ended_at: str = "2026-05-17T00:30:00Z",
    tokens_used: int = 1000,
    cost_usd: float = 0.05,
    model: str = "gpt-5.4",
    role: str = "se",
    related_plan_id: str | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "run_id": run_id,
        "session_id": session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "tokens_used": tokens_used,
        "cost_usd": cost_usd,
        "model": model,
        "role": role,
    }
    if related_plan_id is not None:
        body["related_plan_id"] = related_plan_id
    return body


def _configure_telemetry_db(monkeypatch: pytest.MonkeyPatch, *, run_exists: bool = True):
    fake_conn = MagicMock(name="fake_conn")
    fake_conn.execute.return_value.fetchone.return_value = (1,) if run_exists else None
    upsert_spy = MagicMock(name="upsert_row")

    monkeypatch.setattr(
        telemetry_module.helix_db,
        "resolve_default_db_path",
        MagicMock(return_value="/tmp/helix-telemetry-test.db"),
    )
    monkeypatch.setattr(
        telemetry_module.helix_db,
        "_write_connection",
        lambda _path: _managed_connection(fake_conn),
    )
    monkeypatch.setattr(telemetry_module.helix_db, "_upsert_row", upsert_spy)
    return fake_conn, upsert_spy


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HELIX_HTTP_API_TOKEN", "test-token-abc")
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_require_non_empty_string_returns_value():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-H-001 ("abc" -> "abc")
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_non_empty_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    assert telemetry_module._require_non_empty_string("abc", "field") == "abc"


def test_require_non_empty_string_returns_none_on_none():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-H-002 (None -> None)
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_non_empty_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    assert telemetry_module._require_non_empty_string(None, "field") is None


def test_require_non_empty_string_raises_on_empty_string():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-H-003 ("" -> ValueError)
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_non_empty_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    with pytest.raises(ValueError):
        telemetry_module._require_non_empty_string("", "field")


def test_require_non_empty_string_raises_on_max_overflow():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-H-004 ("a" * 129 -> ValueError)
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_non_empty_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    with pytest.raises(ValueError):
        telemetry_module._require_non_empty_string("a" * 129, "field")


def test_require_timestamp_string_returns_value():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-T-001 ("2026-05-17T00:00:00Z" -> string)
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_timestamp_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    assert telemetry_module._require_timestamp_string("2026-05-17T00:00:00Z", "ts") == "2026-05-17T00:00:00Z"


def test_require_timestamp_string_raises_on_empty_string():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-T-002 ("" -> ValueError)
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_timestamp_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    with pytest.raises(ValueError):
        telemetry_module._require_timestamp_string("", "ts")


def test_require_timestamp_string_raises_on_none():
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-T-003 (None -> ValueError)
    対象実装: cli/lib/http_api/routes/telemetry.py::_require_timestamp_string
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    with pytest.raises(ValueError):
        telemetry_module._require_timestamp_string(None, "ts")


def test_session_telemetry_handler_success_persists_payload(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-001 (normal body -> 200 + UPSERT)
    対象実装: cli/lib/http_api/routes/telemetry.py::session_telemetry
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    _fake_conn, upsert_spy = _configure_telemetry_db(monkeypatch, run_exists=True)
    response = client.post(
        "/api/v1/automation/session/telemetry",
        headers={**_auth_headers("trace-telemetry-001"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_telemetry_body(11, related_plan_id="PLAN-075"),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["data"]["acknowledged"] is True
    assert "persisted_at" in data["data"]
    upsert_spy.assert_called_once()
    args, kwargs = upsert_spy.call_args
    assert args[1] == "session_telemetry"
    assert kwargs["conflict_column"] == "session_id"
    payload = args[2]
    assert payload["session_id"] == "sess-001"
    assert payload["actor"] == "se/gpt-5.4"
    assert payload["tokens_total"] == 1000
    assert payload["cost_usd"] == pytest.approx(0.05)
    assert payload["related_plan_id"] == "PLAN-075"


def test_session_telemetry_handler_missing_fields_returns_400(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-002 (required field missing -> 400)
    対象実装: cli/lib/http_api/routes/telemetry.py::session_telemetry
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    fake_conn, upsert_spy = _configure_telemetry_db(monkeypatch, run_exists=True)
    response = client.post(
        "/api/v1/automation/session/telemetry",
        headers={**_auth_headers("trace-telemetry-002"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json={"run_id": 11, "session_id": "sess-002"},
    )

    assert response.status_code == 400
    assert fake_conn.execute.call_count == 0
    assert upsert_spy.call_count == 0


def test_session_telemetry_handler_unique_violation_is_idempotent(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-003 (UNIQUE violation handled by UPSERT -> 200)
    対象実装: cli/lib/http_api/routes/telemetry.py::session_telemetry
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    stored: dict[str, dict[str, object]] = {}

    def fake_upsert(conn, table, payload, conflict_column):
        key = str(payload["session_id"])
        stored[key] = dict(payload)
        return 1

    fake_conn, _upsert_spy = _configure_telemetry_db(monkeypatch, run_exists=True)
    monkeypatch.setattr(telemetry_module.helix_db, "_upsert_row", fake_upsert)

    response_1 = client.post(
        "/api/v1/automation/session/telemetry",
        headers={**_auth_headers("trace-telemetry-003a"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_telemetry_body(11, session_id="sess-upsert", tokens_used=1000, cost_usd=0.05),
    )
    response_2 = client.post(
        "/api/v1/automation/session/telemetry",
        headers={**_auth_headers("trace-telemetry-003b"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_telemetry_body(11, session_id="sess-upsert", tokens_used=1400, cost_usd=0.10),
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert stored["sess-upsert"]["tokens_total"] == 1400
    assert stored["sess-upsert"]["cost_usd"] == pytest.approx(0.10)
    assert fake_conn.execute.call_count == 2


def test_session_telemetry_handler_sqlite_error_returns_500(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-004 (sqlite Error -> 500)
    対象実装: cli/lib/http_api/routes/telemetry.py::session_telemetry
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    _fake_conn, upsert_spy = _configure_telemetry_db(monkeypatch, run_exists=True)
    upsert_spy.side_effect = sqlite3.Error("db down")
    response = client.post(
        "/api/v1/automation/session/telemetry",
        headers={**_auth_headers("trace-telemetry-004"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_telemetry_body(11),
    )

    assert response.status_code == 500
    upsert_spy.assert_called_once()


def test_session_telemetry_handler_cost_usd_type_invalid_returns_400(client, monkeypatch: pytest.MonkeyPatch):
    """DoD 検証: PLAN-074-unit-test-design.md U-TEL-005 (cost_usd type invalid -> 400)
    対象実装: cli/lib/http_api/routes/telemetry.py::session_telemetry
    対象設計 (①): D-API EXT §3.5 Stop hook telemetry endpoint
    """
    fake_conn, upsert_spy = _configure_telemetry_db(monkeypatch, run_exists=True)
    response = client.post(
        "/api/v1/automation/session/telemetry",
        headers={**_auth_headers("trace-telemetry-005"), "Content-Type": "application/json"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        json=_telemetry_body(11, cost_usd="bad-value"),
    )

    assert response.status_code == 400
    assert fake_conn.execute.call_count == 0
    assert upsert_spy.call_count == 0
