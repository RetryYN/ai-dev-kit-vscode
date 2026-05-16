"""PLAN-080 harness_monitor 単体テスト.

契約: docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §13
DoD 検証: docs/v2/L4-test-design/PLAN-080-unit-test-design.md U-HM-EVENT-001〜U-HM-LIST-006
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import harness_monitor
import helix_db


BASE_NOW = datetime(2026, 5, 17, 12, 0, 0)


def _sqlite_text(dt: datetime) -> str:
    return dt.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _apply_sqlite_now(base_now: datetime, *args: object) -> str:
    current = base_now.replace(microsecond=0)
    values = [str(arg).strip() for arg in args if str(arg).strip()]
    if values and values[0].lower() == "now":
        values = values[1:]
    for value in values:
        if value == "start of day":
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)
            continue
        match = re.fullmatch(r"([+-])(\d+)\s+(second|seconds|minute|minutes|hour|hours|day|days)", value)
        if match is None:
            raise ValueError(f"unsupported sqlite datetime modifier: {value}")
        sign = 1 if match.group(1) == "+" else -1
        amount = int(match.group(2))
        unit = match.group(3)
        if unit.startswith("second"):
            delta = timedelta(seconds=amount)
        elif unit.startswith("minute"):
            delta = timedelta(minutes=amount)
        elif unit.startswith("hour"):
            delta = timedelta(hours=amount)
        else:
            delta = timedelta(days=amount)
        current = current + delta if sign > 0 else current - delta
    return _sqlite_text(current)


def _patch_sqlite_now(monkeypatch: pytest.MonkeyPatch, base_now: datetime) -> None:
    original_connect = helix_db._connect

    def _connect_with_fixed_now(db_path: str | Path):
        conn = original_connect(db_path)
        conn.create_function("datetime", -1, lambda *args: _apply_sqlite_now(base_now, *args))
        return conn

    monkeypatch.setattr(helix_db, "_connect", _connect_with_fixed_now)


def _patch_write_connection(monkeypatch: pytest.MonkeyPatch, base_now: datetime) -> None:
    @contextmanager
    def _write_connection_without_lock(db_path: str | Path | None, ensure_schema: bool = True):
        target_path = helix_db._resolve_db_path(db_path)
        conn = sqlite3.connect(target_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        conn.create_function("datetime", -1, lambda *args: _apply_sqlite_now(base_now, *args))
        try:
            if ensure_schema:
                helix_db._ensure_schema(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    monkeypatch.setattr(helix_db, "_write_connection", _write_connection_without_lock)


def _open_conn(db_path: Path) -> sqlite3.Connection:
    conn = helix_db.get_connection(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _raw_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _seed_fresh_db(db_path: Path) -> None:
    with _raw_conn(db_path) as conn:
        conn.executescript(helix_db.SCHEMA)
        conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
        helix_db.migrate_all(conn)


def _insert_automation_run(
    db_path: Path,
    *,
    run_kind: str = "pr",
    plan_id: str = "PLAN-080",
    trigger_actor: str = "system",
    started_at: str | None = None,
    status: str = "running",
    summary: str | None = None,
) -> int:
    payload = {
        "run_kind": run_kind,
        "plan_id": plan_id,
        "trigger_actor": trigger_actor,
        "started_at": started_at or _sqlite_text(BASE_NOW - timedelta(minutes=10)),
        "ended_at": None,
        "status": status,
        "exit_code": None,
        "summary": summary,
        "retry_count": 0,
        "max_retries": 0,
        "last_error": None,
    }
    columns = list(payload)
    placeholders = ", ".join(["?"] * len(columns))
    with _raw_conn(db_path) as conn:
        cursor = conn.execute(
            f"INSERT INTO automation_runs ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )
        return int(cursor.lastrowid)


def _insert_agent_slot(
    db_path: Path,
    *,
    agent_kind: str = "codex",
    role: str | None = "tl",
    subagent_type: str | None = None,
    plan_id: str | None = None,
    task_id: str | None = None,
    sprint: str | None = None,
    session_id: str | None = None,
    automation_run_id: int | None = None,
    slot_source: str = "helix_codex",
    fired_at: str | None = None,
    released_at: str | None = None,
    status: str = "running",
    exit_code: int | None = None,
) -> int:
    slot_key = f"codex:{role or 'unknown'}" if agent_kind == "codex" else f"subagent:{subagent_type or 'unknown'}"
    payload = {
        "slot_key": slot_key,
        "agent_kind": agent_kind,
        "role": role,
        "subagent_type": subagent_type,
        "plan_id": plan_id,
        "task_id": task_id,
        "sprint": sprint,
        "session_id": session_id,
        "automation_run_id": automation_run_id,
        "fired_at": fired_at or _sqlite_text(BASE_NOW - timedelta(minutes=5)),
        "released_at": released_at,
        "status": status,
        "exit_code": exit_code,
        "slot_source": slot_source,
    }
    columns = list(payload)
    placeholders = ", ".join(["?"] * len(columns))
    with _raw_conn(db_path) as conn:
        cursor = conn.execute(
            f"INSERT INTO agent_slots ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )
        return int(cursor.lastrowid)


def _insert_event(
    db_path: Path,
    *,
    event_kind: str = "pull",
    check_name: str = "check",
    session_id: str | None = None,
    related_slot_id: int | None = None,
    plan_id: str | None = None,
    severity: str = "info",
    payload: dict | None = None,
    user_visible: bool = False,
    triggered_at: str | None = None,
    created_at: str | None = None,
) -> int:
    payload_dict = {
        "event_kind": event_kind,
        "check_name": check_name,
        "triggered_at": triggered_at or _sqlite_text(BASE_NOW - timedelta(minutes=5)),
        "session_id": session_id,
        "related_slot_id": related_slot_id,
        "plan_id": plan_id,
        "severity": severity,
        "payload": None if payload is None else json.dumps(payload, ensure_ascii=False),
        "user_visible": int(bool(user_visible)),
        "created_at": created_at or _sqlite_text(BASE_NOW - timedelta(minutes=5)),
    }
    columns = list(payload_dict)
    placeholders = ", ".join(["?"] * len(columns))
    with _raw_conn(db_path) as conn:
        cursor = conn.execute(
            f"INSERT INTO harness_check_events ({', '.join(columns)}) VALUES ({placeholders})",
            [payload_dict[column] for column in columns],
        )
        return int(cursor.lastrowid)


def _fetch_event(db_path: Path, event_id: int) -> sqlite3.Row:
    conn = _open_conn(db_path)
    try:
        row = conn.execute("SELECT * FROM harness_check_events WHERE id = ?", (event_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _fetch_events(db_path: Path) -> list[sqlite3.Row]:
    conn = _open_conn(db_path)
    try:
        rows = conn.execute("SELECT * FROM harness_check_events ORDER BY id ASC").fetchall()
    finally:
        conn.close()
    return rows


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """fresh SQLite を作成し、HELIX_DB_PATH を temp DB に固定する。"""
    db_path = tmp_path / "test_helix.db"
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    _seed_fresh_db(db_path)
    _patch_sqlite_now(monkeypatch, BASE_NOW)
    _patch_write_connection(monkeypatch, BASE_NOW)
    return db_path


class TestRecordEvent:
    def test_u_hm_event_001_valid_pull_event_returns_row_id(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-001 (pull/info の INSERT が成功し row id を返す)"""
        event_id = harness_monitor.record_event("pull", "slot-overflow")

        row = _fetch_event(fresh_db, event_id)
        assert isinstance(event_id, int)
        assert event_id > 0
        assert row["event_kind"] == "pull"
        assert row["severity"] == "info"
        assert row["check_name"] == "slot-overflow"

    def test_u_hm_event_002_valid_warning_event_persists_session_id(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-002 (push/warning と session_id を保存)"""
        event_id = harness_monitor.record_event("push", "session-summary", session_id="SESSION-001", severity="warning")

        row = _fetch_event(fresh_db, event_id)
        assert row["event_kind"] == "push"
        assert row["session_id"] == "SESSION-001"
        assert row["severity"] == "warning"

    def test_u_hm_event_003_invalid_event_kind_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-003 (event_kind の不正値は ValueError)"""
        with pytest.raises(ValueError, match="invalid event_kind"):
            harness_monitor.record_event("invalid", "slot-overflow")

    def test_u_hm_event_004_invalid_severity_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-004 (severity の不正値は ValueError)"""
        with pytest.raises(ValueError, match="invalid severity"):
            harness_monitor.record_event("audit", "slot-overflow", severity="critical-ish")

    def test_u_hm_event_005_empty_check_name_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-005 (check_name 空文字は ValueError)"""
        with pytest.raises(ValueError, match="check_name must be a non-empty string"):
            harness_monitor.record_event("pull", "   ")

    def test_u_hm_event_006_non_dict_payload_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-006 (payload 非 dict は ValueError)"""
        with pytest.raises(ValueError, match="payload must be a dict or None"):
            harness_monitor.record_event("pull", "slot-overflow", payload="not-a-dict")  # type: ignore[arg-type]

    def test_u_hm_event_007_unserializable_payload_raises_type_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-007 (JSON 化できない payload は TypeError)"""
        with pytest.raises(TypeError):
            harness_monitor.record_event("push", "slot-overflow", payload={"bad": object()})

    def test_u_hm_event_008_related_slot_fk_violation_raises_integrity_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-EVENT-008 (related_slot_id 不整合は IntegrityError)"""
        with pytest.raises(sqlite3.IntegrityError):
            harness_monitor.record_event("audit", "slot-overflow", related_slot_id=99999)


class TestGetActiveStatus:
    def test_u_hm_stat_001_all_sessions_aggregate_active_slots_and_runs(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-STAT-001 (全 session の active 集計を返す)"""
        _insert_automation_run(fresh_db, run_kind="pr", summary="running-pr")
        _insert_automation_run(fresh_db, run_kind="push", status="completed", summary="done")
        _insert_agent_slot(fresh_db, session_id="SESSION-A", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=20)))
        _insert_agent_slot(fresh_db, session_id="SESSION-B", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=10)))

        status = harness_monitor.get_active_status()

        assert status["active_slot_count"] == 2
        assert [row["summary"] for row in status["running_tasks"]] == ["running-pr"]
        assert status["recent_warnings"] == []
        assert status["recent_criticals"] == []
        assert status["peak_parallel_today"] == 2

    def test_u_hm_stat_002_session_filter_limits_active_and_events(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-STAT-002 (session_id で対象 session のみ集計)"""
        _insert_agent_slot(fresh_db, session_id="SESSION-A", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=20)))
        _insert_agent_slot(fresh_db, session_id="SESSION-B", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=10)))
        _insert_event(fresh_db, session_id="SESSION-A", severity="warning", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=1)))
        _insert_event(fresh_db, session_id="SESSION-B", severity="warning", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=1)))

        status = harness_monitor.get_active_status("SESSION-A")

        assert status["active_slot_count"] == 1
        assert len(status["recent_warnings"]) == 1
        assert status["recent_warnings"][0]["session_id"] == "SESSION-A"

    def test_u_hm_stat_003_missing_session_returns_zero_shape(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-STAT-003 (存在しない session は空集計)"""
        status = harness_monitor.get_active_status("MISSING-SESSION")

        assert status["active_slot_count"] == 0
        assert status["running_tasks"] == []
        assert status["recent_warnings"] == []
        assert status["recent_criticals"] == []
        assert status["peak_parallel_today"] == 0

    def test_u_hm_stat_004_no_active_slots_returns_zero_count(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-STAT-004 (active row がなければ 0 件)"""
        status = harness_monitor.get_active_status()

        assert status["active_slot_count"] == 0
        assert status["peak_parallel_today"] == 0

    def test_u_hm_stat_005_mixed_severity_keeps_recent_counts_and_peak(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-STAT-005 (warning / critical 混在でも内訳を維持)"""
        _insert_agent_slot(fresh_db, session_id="SESSION-A", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=30)))
        _insert_agent_slot(fresh_db, session_id="SESSION-A", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=25)))
        _insert_event(fresh_db, session_id="SESSION-A", severity="warning", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=2)))
        _insert_event(fresh_db, session_id="SESSION-A", severity="critical", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=1)))
        _insert_event(fresh_db, session_id="SESSION-A", severity="critical", triggered_at=_sqlite_text(BASE_NOW - timedelta(minutes=30)))

        status = harness_monitor.get_active_status("SESSION-A")

        assert status["active_slot_count"] == 2
        assert len(status["recent_warnings"]) == 1
        assert len(status["recent_criticals"]) == 2
        assert status["peak_parallel_today"] == 2

    def test_u_hm_stat_006_blank_session_is_treated_as_all_sessions(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-STAT-006 (空白 session_id は未指定扱い)"""
        _insert_agent_slot(fresh_db, session_id="SESSION-A", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=20)))
        _insert_agent_slot(fresh_db, session_id="SESSION-B", fired_at=_sqlite_text(BASE_NOW - timedelta(minutes=10)))

        status = harness_monitor.get_active_status("   ")

        assert status["active_slot_count"] == 2


class TestGetSessionAudit:
    def test_u_hm_audit_001_existing_session_summary_counts(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-AUDIT-001 (既存 session の audit summary を返す)"""
        _insert_event(fresh_db, event_kind="pull", session_id="SESSION-A", severity="info", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=3)))
        _insert_event(fresh_db, event_kind="push", session_id="SESSION-A", severity="warning", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=2)))
        _insert_event(fresh_db, event_kind="audit", session_id="SESSION-A", severity="critical", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=1)))

        audit = harness_monitor.get_session_audit("SESSION-A")

        assert audit["session_id"] == "SESSION-A"
        assert audit["total_events"] == 3
        assert audit["by_kind"] == {"pull": 1, "push": 1, "audit": 1}
        assert audit["by_severity"] == {"info": 1, "warning": 1, "critical": 1}
        assert audit["first_event_at"] == _sqlite_text(BASE_NOW - timedelta(hours=3))
        assert audit["last_event_at"] == _sqlite_text(BASE_NOW - timedelta(hours=1))

    def test_u_hm_audit_002_mixed_severity_counts_are_correct(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-AUDIT-002 (severity 混在でも件数が崩れない)"""
        _insert_event(fresh_db, event_kind="pull", session_id="SESSION-B", severity="info")
        _insert_event(fresh_db, event_kind="pull", session_id="SESSION-B", severity="warning")
        _insert_event(fresh_db, event_kind="push", session_id="SESSION-B", severity="critical")

        audit = harness_monitor.get_session_audit("SESSION-B")

        assert audit["by_severity"] == {"info": 1, "warning": 1, "critical": 1}

    def test_u_hm_audit_003_multiple_event_kinds_are_counted(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-AUDIT-003 (event_kind 別件数を集計)"""
        _insert_event(fresh_db, event_kind="pull", session_id="SESSION-C")
        _insert_event(fresh_db, event_kind="pull", session_id="SESSION-C")
        _insert_event(fresh_db, event_kind="push", session_id="SESSION-C")
        _insert_event(fresh_db, event_kind="audit", session_id="SESSION-C")

        audit = harness_monitor.get_session_audit("SESSION-C")

        assert audit["total_events"] == 4
        assert audit["by_kind"] == {"pull": 2, "push": 1, "audit": 1}

    def test_u_hm_audit_004_none_session_id_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-AUDIT-004 (None session_id は現状 'None' として集計)"""
        audit = harness_monitor.get_session_audit(None)  # type: ignore[arg-type]

        assert audit["session_id"] == "None"
        assert audit["total_events"] == 0

    def test_u_hm_audit_005_empty_session_id_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-AUDIT-005 (空文字 session_id は ValueError)"""
        with pytest.raises(ValueError, match="session_id must be a non-empty string"):
            harness_monitor.get_session_audit("  ")

    def test_u_hm_audit_006_empty_session_returns_zero_summary(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-AUDIT-006 (event 0 件の session は 0 summary)"""
        audit = harness_monitor.get_session_audit("SESSION-Z")

        assert audit["session_id"] == "SESSION-Z"
        assert audit["total_events"] == 0
        assert audit["by_kind"] == {"pull": 0, "push": 0, "audit": 0}
        assert audit["by_severity"] == {"info": 0, "warning": 0, "critical": 0}
        assert audit["first_event_at"] is None
        assert audit["last_event_at"] is None


class TestListRecentEvents:
    def test_u_hm_list_001_days_seven_returns_recent_events_descending(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-LIST-001 (7 日 window の全 event を返す)"""
        old_event = _insert_event(fresh_db, event_kind="pull", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(days=6, hours=23, minutes=59)))
        in_window_event = _insert_event(fresh_db, event_kind="push", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(days=1)))
        newest_event = _insert_event(fresh_db, event_kind="audit", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=1)))
        _insert_event(fresh_db, event_kind="audit", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(days=7, minutes=1)))

        events = harness_monitor.list_recent_events(days=7)

        assert [row["id"] for row in events] == [newest_event, in_window_event, old_event]
        assert all(row["triggered_at"] >= _sqlite_text(BASE_NOW - timedelta(days=7)) for row in events)

    def test_u_hm_list_002_days_one_warning_only(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-LIST-002 (1 日 window + warning のみ)"""
        warning_id = _insert_event(
            fresh_db,
            event_kind="pull",
            session_id="SESSION-A",
            severity="warning",
            triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=3)),
        )
        _insert_event(
            fresh_db,
            event_kind="push",
            session_id="SESSION-A",
            severity="info",
            triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=2)),
        )
        _insert_event(
            fresh_db,
            event_kind="audit",
            session_id="SESSION-A",
            severity="warning",
            triggered_at=_sqlite_text(BASE_NOW - timedelta(days=2)),
        )

        events = harness_monitor.list_recent_events(days=1, severity="warning")

        assert [row["id"] for row in events] == [warning_id]
        assert all(row["severity"] == "warning" for row in events)

    def test_u_hm_list_003_days_zero_returns_today_only(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-LIST-003 (days=0 は当日分のみ)"""
        today_event = _insert_event(fresh_db, event_kind="pull", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(hours=2)))
        _insert_event(fresh_db, event_kind="push", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(days=1, minutes=1)))

        events = harness_monitor.list_recent_events(days=0)

        assert [row["id"] for row in events] == [today_event]
        assert all(row["triggered_at"] >= _sqlite_text(BASE_NOW.replace(hour=0, minute=0, second=0)) for row in events)

    def test_u_hm_list_004_negative_days_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-LIST-004 (days 負値は ValueError)"""
        with pytest.raises(ValueError, match="days must be a non-negative integer"):
            harness_monitor.list_recent_events(days=-1)

    def test_u_hm_list_005_large_days_still_filters_all_available_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-LIST-005 (大きな days でも正常に絞り込む)"""
        early_event = _insert_event(fresh_db, event_kind="pull", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(days=10)))
        late_event = _insert_event(fresh_db, event_kind="push", session_id="SESSION-A", triggered_at=_sqlite_text(BASE_NOW - timedelta(days=2)))

        events = harness_monitor.list_recent_events(days=30)

        assert [row["id"] for row in events] == [late_event, early_event]

    def test_u_hm_list_006_invalid_severity_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-080-unit-test-design.md U-HM-LIST-006 (severity 不正値は ValueError)"""
        with pytest.raises(ValueError, match="invalid severity"):
            harness_monitor.list_recent_events(days=1, severity="bad")
