"""
PLAN-080 harness_monitor 結合テスト (Python 層)
契約: docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §13 + PLAN-080 §3.1-§3.3
DoD 検証: docs/v2/L4-test-design/PLAN-080-integration-test-design.md
        I-PULL-001 / I-FK-001〜I-FK-003 / I-PAYLOAD-001〜I-PAYLOAD-003
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import agent_slots
import harness_monitor
import helix_db


def _init_integration_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    helix_db.init_db(str(db_path))
    return db_path


def _seed_automation_run(
    db_path: Path,
    *,
    run_kind: str,
    trigger_actor: str,
    started_at: str,
    status: str,
    summary: str | None = None,
    ended_at: str | None = None,
    exit_code: int | None = None,
    plan_id: str = "PLAN-080",
) -> int:
    with helix_db._write_connection(str(db_path)) as conn:
        cursor = conn.execute(
            """
            INSERT INTO automation_runs (
                run_kind, plan_id, trigger_actor, started_at, ended_at, status, exit_code, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_kind, plan_id, trigger_actor, started_at, ended_at, status, exit_code, summary),
        )
        return int(cursor.lastrowid)


def _seed_agent_slot(
    db_path: Path,
    *,
    agent_kind: str,
    role: str | None = None,
    subagent_type: str | None = None,
    plan_id: str | None = None,
    task_id: str | None = None,
    sprint: str | None = None,
    session_id: str | None = None,
    automation_run_id: int | None = None,
) -> int:
    with helix_db._write_connection(str(db_path)) as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_slots (
                slot_key, agent_kind, role, subagent_type, plan_id, task_id, sprint,
                session_id, automation_run_id, status, slot_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', 'helix_codex')
            """,
            (
                agent_slots._build_slot_key(agent_kind, role, subagent_type),
                agent_kind,
                role,
                subagent_type,
                plan_id,
                task_id,
                sprint,
                session_id,
                automation_run_id,
            ),
        )
        return int(cursor.lastrowid)


def _query_row(db_path: Path, sql: str, params: tuple[object, ...]) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


class TestHarnessMonitorIntegration:
    def test_i_pull_001_get_active_status_filters_session_and_collects_events(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-PULL-001: active slot / running task / recent event の集計を session 単位で確認する。"""
        db_path = _init_integration_db(tmp_path, monkeypatch)
        _seed_automation_run(
            db_path,
            run_kind="helix-push",
            trigger_actor="system",
            started_at="2026-05-17 11:00:00",
            status="running",
            summary='{"phase":"push"}',
        )
        _seed_automation_run(
            db_path,
            run_kind="helix-push",
            trigger_actor="system",
            started_at="2026-05-17 11:05:00",
            status="completed",
            ended_at="2026-05-17 11:10:00",
            exit_code=0,
            summary='{"phase":"done"}',
        )
        slot_a = _seed_agent_slot(
            db_path,
            agent_kind="codex",
            role="pg",
            plan_id="PLAN-080",
            task_id="TASK-001",
            sprint=".4",
            session_id="sess-001",
            automation_run_id=1,
        )
        _seed_agent_slot(
            db_path,
            agent_kind="claude_subagent",
            subagent_type="watchdog",
            plan_id="PLAN-080",
            task_id="TASK-002",
            sprint=".4",
            session_id="sess-001",
            automation_run_id=1,
        )
        _seed_agent_slot(
            db_path,
            agent_kind="codex",
            role="qa",
            plan_id="PLAN-080",
            task_id="TASK-999",
            sprint=".4",
            session_id="sess-other",
            automation_run_id=1,
        )

        harness_monitor.record_event(
            "pull",
            "status_viewed",
            session_id="sess-001",
            related_slot_id=slot_a,
            severity="warning",
            payload={"session": "sess-001", "slot_count": 2},
        )
        harness_monitor.record_event(
            "audit",
            "session_summary",
            session_id="sess-001",
            related_slot_id=slot_a,
            severity="critical",
            payload={"summary": {"active": 2, "warnings": 1}},
        )
        harness_monitor.record_event(
            "pull",
            "status_viewed",
            session_id="sess-other",
            severity="warning",
            payload={"session": "sess-other"},
        )

        status = harness_monitor.get_active_status(session_id="sess-001")

        assert status["active_slot_count"] == 2
        assert len(status["running_tasks"]) == 1
        assert status["running_tasks"][0]["run_kind"] == "helix-push"
        assert status["running_tasks"][0]["status"] == "running"
        assert len(status["recent_warnings"]) == 1
        assert len(status["recent_criticals"]) == 1
        assert status["recent_warnings"][0]["payload"] == {"session": "sess-001", "slot_count": 2}
        assert status["recent_criticals"][0]["payload"] == {"summary": {"active": 2, "warnings": 1}}
        assert status["peak_parallel_today"] >= 2

    def test_i_fk_001_record_event_links_to_existing_agent_slot(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-FK-001: related_slot_id に既存 slot を指定すると FK が保存される。"""
        db_path = _init_integration_db(tmp_path, monkeypatch)
        slot_id = _seed_agent_slot(
            db_path,
            agent_kind="codex",
            role="se",
            plan_id="PLAN-080",
            task_id="TASK-010",
            sprint=".4",
            session_id="sess-010",
        )

        event_id = harness_monitor.record_event(
            "push",
            "slot_count_warning",
            session_id="sess-010",
            related_slot_id=slot_id,
            severity="warning",
            payload={"active": 6},
            user_visible=True,
        )

        row = _query_row(
            db_path,
            "SELECT related_slot_id, event_kind, severity, user_visible FROM harness_check_events WHERE id = ?",
            (event_id,),
        )
        assert row["related_slot_id"] == slot_id
        assert row["event_kind"] == "push"
        assert row["severity"] == "warning"
        assert row["user_visible"] == 1

    def test_i_fk_002_record_event_rejects_missing_agent_slot(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-FK-002: 存在しない related_slot_id は sqlite3.IntegrityError で拒否される。"""
        _init_integration_db(tmp_path, monkeypatch)

        with pytest.raises(sqlite3.IntegrityError):
            harness_monitor.record_event(
                "audit",
                "missing_slot_reference",
                related_slot_id=999999,
                severity="critical",
                payload={"slot": 999999},
            )

    def test_i_fk_003_record_event_allows_null_related_slot_for_pull_only(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-FK-003: pull-only event は related_slot_id=None のまま保存できる。"""
        db_path = _init_integration_db(tmp_path, monkeypatch)

        event_id = harness_monitor.record_event(
            "pull",
            "status_viewed",
            session_id="sess-020",
            related_slot_id=None,
            severity="info",
            payload={"json": True},
        )

        row = _query_row(
            db_path,
            "SELECT related_slot_id, event_kind, payload FROM harness_check_events WHERE id = ?",
            (event_id,),
        )
        assert row["related_slot_id"] is None
        assert row["event_kind"] == "pull"
        assert json.loads(row["payload"]) == {"json": True}

    def test_i_payload_001_record_event_preserves_payload_json_text(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-PAYLOAD-001: payload は DB 上で JSON 文字列として保持される。"""
        db_path = _init_integration_db(tmp_path, monkeypatch)
        payload = {
            "slot_count": 3,
            "parallel_ratio": 0.5,
            "nested": {"active": [1, 2, 3]},
        }

        event_id = harness_monitor.record_event(
            "audit",
            "payload_snapshot",
            session_id="sess-030",
            severity="info",
            payload=payload,
        )

        row = _query_row(
            db_path,
            "SELECT payload FROM harness_check_events WHERE id = ?",
            (event_id,),
        )
        assert isinstance(row["payload"], str)
        assert row["payload"] == json.dumps(payload, ensure_ascii=False)

    def test_i_payload_002_record_event_round_trips_payload_structure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-PAYLOAD-002: list_recent_events で payload の構造が壊れず復元される。"""
        _init_integration_db(tmp_path, monkeypatch)
        payload = {
            "current": {"slot_count": 2},
            "recent": [{"kind": "pull", "id": 1}, {"kind": "audit", "id": 2}],
        }

        harness_monitor.record_event(
            "push",
            "payload_round_trip",
            session_id="sess-040",
            severity="warning",
            payload=payload,
        )

        events = harness_monitor.list_recent_events(days=1, severity="warning")

        assert len(events) == 1
        assert events[0]["check_name"] == "payload_round_trip"
        assert events[0]["payload"] == payload
        assert events[0]["user_visible"] is False

    def test_i_payload_003_list_recent_events_parses_json_payload(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-PAYLOAD-003: recent event の payload が dict に parse される。"""
        _init_integration_db(tmp_path, monkeypatch)
        harness_monitor.record_event(
            "audit",
            "payload_parse",
            session_id="sess-050",
            severity="critical",
            payload={"current": {"slot_count": 4}, "status": "ok"},
            user_visible=True,
        )

        events = harness_monitor.list_recent_events(days=1, severity="critical")

        assert len(events) == 1
        assert events[0]["payload"] == {"current": {"slot_count": 4}, "status": "ok"}
        assert events[0]["user_visible"] is True
