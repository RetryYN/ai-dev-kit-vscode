"""PLAN-078 agent_slots 単体テスト.

契約: docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §10 (agent_slots)
DoD 検証: docs/v2/L4-test-design/PLAN-078-unit-test-design.md U-FIRE-001〜U-STATS-012
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import agent_slots
import helix_db


def _iso_utc(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat(sep=" ")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _shifted_iso(*, days: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    return _iso_utc(_now_utc() - timedelta(days=days, minutes=minutes, seconds=seconds))


def _open_conn(db_path: Path) -> sqlite3.Connection:
    conn = helix_db.get_connection(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _seed_fresh_db(db_path: Path) -> None:
    with helix_db._write_connection(str(db_path), ensure_schema=False) as conn:
        conn.executescript(helix_db.SCHEMA)
        conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
        helix_db.migrate_all(conn)


def _fetch_slot(db_path: Path, slot_id: int) -> sqlite3.Row:
    conn = _open_conn(db_path)
    try:
        row = conn.execute("SELECT * FROM agent_slots WHERE id = ?", (slot_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _insert_automation_run(db_path: Path, trigger_source: str = "test", run_kind: str = "pr") -> int:
    conn = _open_conn(db_path)
    try:
        run_id = helix_db.insert_automation_run(conn, trigger_source, run_kind, {"plan_id": "PLAN-078"})
        conn.commit()
    finally:
        conn.close()
    return run_id


def _seed_slot(
    db_path: Path,
    *,
    agent_kind: str = "codex",
    role: str | None = None,
    subagent_type: str | None = None,
    plan_id: str | None = None,
    task_id: str | None = None,
    sprint: str | None = None,
    session_id: str | None = None,
    automation_run_id: int | None = None,
    slot_source: str = "helix_codex",
    status: str = "running",
    fired_at: str | None = None,
    released_at: str | None = None,
    exit_code: int | None = None,
) -> int:
    slot_key = f"codex:{(role.strip() if isinstance(role, str) and role.strip() else 'unknown')}" if agent_kind == "codex" else f"subagent:{(subagent_type.strip() if isinstance(subagent_type, str) and subagent_type.strip() else 'unknown')}"
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
        "fired_at": fired_at or _shifted_iso(),
        "released_at": released_at,
        "status": status,
        "exit_code": exit_code,
        "slot_source": slot_source,
    }
    columns = list(payload.keys())
    placeholders = ", ".join(["?"] * len(columns))
    with helix_db._write_connection(str(db_path)) as conn:
        cursor = conn.execute(
            f"INSERT INTO agent_slots ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )
        slot_id = int(cursor.lastrowid)
    return slot_id


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """fresh SQLite を作成し、HELIX_DB_PATH を temp DB に固定する。"""
    db_path = tmp_path / "test_helix.db"
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    _seed_fresh_db(db_path)
    return db_path


class TestFireSlot:
    def test_u_fire_001_codex_role_tl(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-001 (codex + role=tl + plan_id で slot_id 生成)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="tl", plan_id="PLAN-078")

        row = _fetch_slot(fresh_db, slot_id)
        assert isinstance(slot_id, int)
        assert slot_id > 0
        assert row["agent_kind"] == "codex"
        assert row["role"] == "tl"
        assert row["plan_id"] == "PLAN-078"

    def test_u_fire_002_claude_subagent_with_type(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-002 (claude_subagent + subagent_type で slot_id 生成)"""
        slot_id = agent_slots.fire_slot(agent_kind="claude_subagent", subagent_type="pmo-sonnet")

        row = _fetch_slot(fresh_db, slot_id)
        assert isinstance(slot_id, int)
        assert slot_id > 0
        assert row["agent_kind"] == "claude_subagent"
        assert row["subagent_type"] == "pmo-sonnet"

    def test_u_fire_003_empty_agent_kind_raises(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-003 (agent_kind 空文字は ValueError)"""
        with pytest.raises(ValueError, match="invalid agent_kind"):
            agent_slots.fire_slot(agent_kind="")

    def test_u_fire_004_none_agent_kind_raises(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-004 (agent_kind=None は ValueError)"""
        with pytest.raises(ValueError, match="invalid agent_kind"):
            agent_slots.fire_slot(agent_kind=None)  # type: ignore[arg-type]

    def test_u_fire_005_codex_without_role_uses_unknown_slot_key(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-005 (role=None / subagent_type=None でも codex slot を作成)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex")

        row = _fetch_slot(fresh_db, slot_id)
        assert row["slot_key"] == "codex:unknown"
        assert row["role"] is None
        assert row["subagent_type"] is None

    def test_u_fire_006_both_role_and_subagent_type_persist(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-006 (role と subagent_type を両方指定しても保存)"""
        slot_id = agent_slots.fire_slot(
            agent_kind="codex",
            role="tl",
            subagent_type="pmo-haiku",
        )

        row = _fetch_slot(fresh_db, slot_id)
        assert row["slot_key"] == "codex:tl"
        assert row["role"] == "tl"
        assert row["subagent_type"] == "pmo-haiku"

    def test_u_fire_007_empty_plan_id_normalizes_to_null(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-007 (plan_id 空文字は NULL に正規化)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", plan_id="   ")

        row = _fetch_slot(fresh_db, slot_id)
        assert row["plan_id"] is None

    def test_u_fire_008_task_sprint_session_are_persisted(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-008 (task_id / sprint / session_id を同時保存)"""
        slot_id = agent_slots.fire_slot(
            agent_kind="codex",
            role="pg",
            task_id="TASK-123",
            sprint=".4",
            session_id="SESSION-001",
        )

        row = _fetch_slot(fresh_db, slot_id)
        assert row["task_id"] == "TASK-123"
        assert row["sprint"] == ".4"
        assert row["session_id"] == "SESSION-001"

    def test_u_fire_009_existing_automation_run_fk_passes(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-009 (automation_run_id の FK が存在すれば INSERT 成功)"""
        run_id = _insert_automation_run(fresh_db)
        slot_id = agent_slots.fire_slot(agent_kind="codex", automation_run_id=run_id)

        row = _fetch_slot(fresh_db, slot_id)
        assert row["automation_run_id"] == run_id

    def test_u_fire_010_missing_automation_run_fk_raises_integrity_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-010 (automation_run_id 不整合は IntegrityError)"""
        with pytest.raises(sqlite3.IntegrityError):
            agent_slots.fire_slot(agent_kind="codex", automation_run_id=99999)

    def test_u_fire_011_consecutive_fire_returns_distinct_ids(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-011 (連続 fire で別 slot_id を返す)"""
        first_id = agent_slots.fire_slot(agent_kind="codex", role="tl")
        second_id = agent_slots.fire_slot(agent_kind="codex", role="se")

        assert first_id != second_id
        assert second_id > first_id

    def test_u_fire_012_default_slot_source_is_saved(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-FIRE-012 (slot_source 既定値は helix_codex)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="qa")

        row = _fetch_slot(fresh_db, slot_id)
        assert row["slot_source"] == "helix_codex"


class TestReleaseSlot:
    def test_u_rel_001_completed_normal_sets_released_at(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-001 (completed で release_at と status を更新)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="tl")

        agent_slots.release_slot(slot_id, status="completed", exit_code=0)

        row = _fetch_slot(fresh_db, slot_id)
        assert row["status"] == "completed"
        assert row["released_at"] is not None
        assert row["exit_code"] == 0

    def test_u_rel_002_failed_status_persists_exit_code(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-002 (failed で status と exit_code を保存)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="se")

        agent_slots.release_slot(slot_id, status="failed", exit_code=1)

        row = _fetch_slot(fresh_db, slot_id)
        assert row["status"] == "failed"
        assert row["exit_code"] == 1

    def test_u_rel_003_cancelled_status_persists(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-003 (cancelled を保存)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="pg")

        agent_slots.release_slot(slot_id, status="cancelled", exit_code=2)

        row = _fetch_slot(fresh_db, slot_id)
        assert row["status"] == "cancelled"
        assert row["exit_code"] == 2

    def test_u_rel_004_missing_slot_id_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-004 (存在しない slot_id は ValueError)"""
        with pytest.raises(ValueError, match="slot_id does not exist"):
            agent_slots.release_slot(99999)

    def test_u_rel_005_releasing_completed_slot_is_rejected(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-005 (既に completed の slot は再 release できない)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="tl")
        agent_slots.release_slot(slot_id, status="completed")

        with pytest.raises(sqlite3.IntegrityError, match="slot is not running"):
            agent_slots.release_slot(slot_id, status="completed")

    def test_u_rel_006_exit_code_none_is_allowed(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-006 (exit_code=None を許容)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="qa")

        agent_slots.release_slot(slot_id, status="completed", exit_code=None)

        row = _fetch_slot(fresh_db, slot_id)
        assert row["status"] == "completed"
        assert row["exit_code"] is None

    def test_u_rel_007_empty_status_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-007 (status 空文字は ValueError)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="tl")

        with pytest.raises(ValueError, match="invalid status"):
            agent_slots.release_slot(slot_id, status="")

    def test_u_rel_008_invalid_status_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-008 (status=timed_out は拒否)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="tl")

        with pytest.raises(ValueError, match="invalid status"):
            agent_slots.release_slot(slot_id, status="timed_out")

    def test_u_rel_009_append_only_delete_trigger_is_preserved(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-009 (release 後も DELETE 禁止 trigger を維持)"""
        slot_id = agent_slots.fire_slot(agent_kind="codex", role="tl")
        agent_slots.release_slot(slot_id, status="completed")

        conn = _open_conn(fresh_db)
        try:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                conn.execute("DELETE FROM agent_slots WHERE id = ?", (slot_id,))
        finally:
            conn.close()

    def test_u_rel_010_release_keeps_timestamp_order(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-REL-010 (released_at は fired_at 以後になる)"""
        slot_id = _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=10),
        )

        agent_slots.release_slot(slot_id, status="completed", exit_code=0)

        row = _fetch_slot(fresh_db, slot_id)
        assert row["released_at"] is not None
        assert row["released_at"] >= row["fired_at"]


class TestListActiveSlots:
    def test_u_list_001_running_only_among_mixed_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-001 (running だけを返す)"""
        first = _seed_slot(fresh_db, agent_kind="codex", role="tl", fired_at=_shifted_iso(minutes=12))
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="se",
            status="completed",
            fired_at=_shifted_iso(minutes=11),
            released_at=_shifted_iso(minutes=10),
            exit_code=0,
        )
        second = _seed_slot(fresh_db, agent_kind="claude_subagent", subagent_type="pmo-sonnet", fired_at=_shifted_iso(minutes=9))

        rows = agent_slots.list_active_slots()

        assert [row["id"] for row in rows] == [first, second]
        assert all(row["status"] == "running" for row in rows)

    def test_u_list_002_no_running_returns_empty_list(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-002 (running がなければ空 list)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            status="completed",
            fired_at=_shifted_iso(minutes=10),
            released_at=_shifted_iso(minutes=9),
        )

        assert agent_slots.list_active_slots() == []

    def test_u_list_003_returns_all_running_without_plan_filter(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-003 (plan_id で絞らず全 running を返す)"""
        first = _seed_slot(fresh_db, agent_kind="codex", role="tl", plan_id="PLAN-A")
        second = _seed_slot(fresh_db, agent_kind="codex", role="se", plan_id="PLAN-B")

        rows = agent_slots.list_active_slots()

        assert {row["id"] for row in rows} == {first, second}

    def test_u_list_004_order_is_stable_by_fired_at_then_id(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-004 (fired_at / id の安定順で返す)"""
        older = _seed_slot(fresh_db, agent_kind="codex", role="tl", fired_at=_shifted_iso(minutes=20))
        newer = _seed_slot(fresh_db, agent_kind="codex", role="se", fired_at=_shifted_iso(minutes=10))

        rows = agent_slots.list_active_slots()

        assert [row["id"] for row in rows] == [older, newer]

    def test_u_list_005_failed_rows_are_excluded(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-005 (failed を除外)"""
        active = _seed_slot(fresh_db, agent_kind="codex", role="tl")
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="se",
            status="failed",
            fired_at=_shifted_iso(minutes=8),
            released_at=_shifted_iso(minutes=7),
            exit_code=1,
        )

        rows = agent_slots.list_active_slots()

        assert [row["id"] for row in rows] == [active]

    def test_u_list_006_running_with_released_at_null_is_included(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-006 (released_at NULL の running は active)"""
        slot_id = _seed_slot(fresh_db, agent_kind="codex", role="qa", released_at=None)

        rows = agent_slots.list_active_slots()

        assert [row["id"] for row in rows] == [slot_id]

    def test_u_list_007_row_shape_contains_agent_slots_columns(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-007 (dict 返却の主要列を保持)"""
        slot_id = _seed_slot(
            fresh_db,
            agent_kind="claude_subagent",
            subagent_type="pmo-haiku",
            plan_id="PLAN-078",
            task_id="TASK-007",
            sprint=".4",
            session_id="SESSION-007",
        )

        row = agent_slots.list_active_slots()[0]

        assert row["id"] == slot_id
        assert {"id", "slot_key", "agent_kind", "role", "subagent_type", "plan_id", "task_id", "sprint", "session_id", "automation_run_id", "fired_at", "released_at", "status", "exit_code", "slot_source"} <= set(row.keys())

    def test_u_list_008_released_running_row_is_not_active(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-LIST-008 (released_at が入った row は active から外れる)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            released_at=_shifted_iso(minutes=1),
        )

        assert agent_slots.list_active_slots() == []


class TestListStaleSlots:
    def test_u_stale_001_under_five_minutes_is_not_stale(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-001 (4 分台は stale でない)"""
        _seed_slot(fresh_db, agent_kind="codex", role="tl", fired_at=_shifted_iso(minutes=4, seconds=59))

        assert agent_slots.list_stale_slots() == []

    def test_u_stale_002_exactly_five_minutes_is_stale(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-002 (5 分境界の stale 側を含める)"""
        slot_id = _seed_slot(fresh_db, agent_kind="codex", role="se", fired_at=_shifted_iso(minutes=5, seconds=1))

        rows = agent_slots.list_stale_slots()

        assert [row["id"] for row in rows] == [slot_id]

    def test_u_stale_003_over_five_minutes_is_stale(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-003 (5 分超は stale)"""
        slot_id = _seed_slot(fresh_db, agent_kind="claude_subagent", subagent_type="pmo-sonnet", fired_at=_shifted_iso(minutes=6))

        rows = agent_slots.list_stale_slots()

        assert [row["id"] for row in rows] == [slot_id]

    def test_u_stale_004_completed_rows_are_excluded(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-004 (completed は stale から除外)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            status="completed",
            fired_at=_shifted_iso(minutes=10),
            released_at=_shifted_iso(minutes=9),
        )

        assert agent_slots.list_stale_slots() == []

    def test_u_stale_005_cancelled_rows_are_excluded(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-005 (cancelled は stale から除外)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            status="cancelled",
            fired_at=_shifted_iso(minutes=10),
            released_at=_shifted_iso(minutes=9),
            exit_code=130,
        )

        assert agent_slots.list_stale_slots() == []

    def test_u_stale_006_threshold_zero_returns_all_running(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-006 (threshold=0 で全 running を候補化)"""
        first = _seed_slot(fresh_db, agent_kind="codex", role="tl", fired_at=_shifted_iso(minutes=1))
        second = _seed_slot(fresh_db, agent_kind="codex", role="se", fired_at=_shifted_iso(seconds=30))

        rows = agent_slots.list_stale_slots(threshold_minutes=0)

        assert [row["id"] for row in rows] == [first, second]

    def test_u_stale_007_negative_threshold_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-007 (threshold_minutes=-1 は ValueError)"""
        with pytest.raises(ValueError, match="threshold_minutes must be a non-negative integer"):
            agent_slots.list_stale_slots(threshold_minutes=-1)

    def test_u_stale_008_none_threshold_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-008 (threshold_minutes=None は ValueError)"""
        with pytest.raises(ValueError, match="threshold_minutes must be a non-negative integer"):
            agent_slots.list_stale_slots(threshold_minutes=None)  # type: ignore[arg-type]

    def test_u_stale_009_returns_oldest_first(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-009 (古い順で返す)"""
        older = _seed_slot(fresh_db, agent_kind="codex", role="tl", fired_at=_shifted_iso(minutes=9))
        newer = _seed_slot(fresh_db, agent_kind="codex", role="se", fired_at=_shifted_iso(minutes=7))

        rows = agent_slots.list_stale_slots()

        assert [row["id"] for row in rows] == [older, newer]

    def test_u_stale_010_released_rows_are_excluded_even_if_old(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STALE-010 (released_at がある row は stale から除外)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=15),
            released_at=_shifted_iso(minutes=14),
            status="completed",
        )

        assert agent_slots.list_stale_slots() == []


class TestGetStats:
    def test_u_stats_001_hour_grouping_returns_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-001 (by=hour の集計を返す)"""
        slot_id = _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=20),
            released_at=_shifted_iso(minutes=18),
            status="completed",
            exit_code=0,
        )

        rows = agent_slots.get_stats(days=7, by="hour")

        assert rows
        assert rows[0]["group"] == _fetch_slot(fresh_db, slot_id)["fired_at"][:13] + ":00:00"
        assert rows[0]["total"] == 1

    def test_u_stats_002_days_one_limits_old_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-002 (days=1 で古い row を除外)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=30),
            released_at=_shifted_iso(minutes=25),
            status="completed",
        )
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="se",
            fired_at=_shifted_iso(days=2, minutes=10),
            released_at=_shifted_iso(days=2, minutes=9),
            status="completed",
        )

        rows = agent_slots.get_stats(days=1, by="role")

        assert [row["group"] for row in rows] == ["tl"]
        assert rows[0]["total"] == 1
        assert rows[0]["group"] == "tl"

    def test_u_stats_003_by_agent_kind_groups(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-003 (by=agent_kind の集計)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=15),
            released_at=_shifted_iso(minutes=14),
            status="completed",
        )
        _seed_slot(
            fresh_db,
            agent_kind="claude_subagent",
            subagent_type="pmo-sonnet",
            fired_at=_shifted_iso(minutes=12),
            released_at=_shifted_iso(minutes=11),
            status="failed",
            exit_code=1,
        )

        rows = agent_slots.get_stats(days=7, by="agent_kind")

        assert [row["group"] for row in rows] == ["claude_subagent", "codex"]
        assert rows[0]["failed"] == 1
        assert rows[1]["completed"] == 1

    def test_u_stats_004_by_role_groups(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-004 (by=role の集計)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=14),
            released_at=_shifted_iso(minutes=13),
            status="completed",
        )
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="se",
            fired_at=_shifted_iso(minutes=10),
            released_at=_shifted_iso(minutes=9),
            status="cancelled",
            exit_code=130,
        )

        rows = agent_slots.get_stats(days=7, by="role")

        assert [row["group"] for row in rows] == ["se", "tl"]
        assert rows[0]["cancelled"] == 1
        assert rows[1]["completed"] == 1

    def test_u_stats_005_by_plan_id_groups(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-005 (by=plan_id の集計)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            plan_id="PLAN-078",
            fired_at=_shifted_iso(minutes=18),
            released_at=_shifted_iso(minutes=17),
            status="completed",
        )
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="se",
            plan_id=None,
            fired_at=_shifted_iso(minutes=16),
            released_at=_shifted_iso(minutes=15),
            status="failed",
            exit_code=1,
        )

        rows = agent_slots.get_stats(days=7, by="plan_id")

        assert [row["group"] for row in rows] == ["(none)", "PLAN-078"]
        assert rows[0]["failed"] == 1
        assert rows[1]["completed"] == 1

    def test_u_stats_006_empty_by_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-006 (by 空文字は ValueError)"""
        with pytest.raises(ValueError, match="invalid by"):
            agent_slots.get_stats(by="")

    def test_u_stats_007_unknown_by_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-007 (by=unknown は ValueError)"""
        with pytest.raises(ValueError, match="invalid by"):
            agent_slots.get_stats(by="unknown")

    def test_u_stats_008_days_zero_is_accepted(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-008 (days=0 を受け入れる)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(seconds=1),
            released_at=_shifted_iso(seconds=1),
            status="completed",
        )

        rows = agent_slots.get_stats(days=0, by="role")

        assert isinstance(rows, list)

    def test_u_stats_009_negative_days_raises_value_error(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-009 (days=-1 は ValueError)"""
        with pytest.raises(ValueError, match="days must be a non-negative integer"):
            agent_slots.get_stats(days=-1)

    def test_u_stats_010_status_breakdown_is_preserved(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-010 (status 別内訳を保つ)"""
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=20),
            released_at=_shifted_iso(minutes=19),
            status="completed",
        )
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=18),
            released_at=_shifted_iso(minutes=17),
            status="failed",
            exit_code=1,
        )
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="tl",
            fired_at=_shifted_iso(minutes=16),
            released_at=_shifted_iso(minutes=15),
            status="cancelled",
            exit_code=130,
        )

        rows = agent_slots.get_stats(days=7, by="role")

        assert rows[0]["completed"] == 1
        assert rows[0]["failed"] == 1
        assert rows[0]["cancelled"] == 1

    def test_u_stats_011_average_duration_is_rounded(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-011 (avg_duration_s を丸める)"""
        group_name = "tl"
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role=group_name,
            fired_at=_shifted_iso(minutes=30),
            released_at=_shifted_iso(minutes=29),
            status="completed",
        )
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role=group_name,
            fired_at=_shifted_iso(minutes=28),
            released_at=_shifted_iso(minutes=26),
            status="completed",
        )

        rows = agent_slots.get_stats(days=7, by="role")

        assert rows[0]["avg_duration_s"] == 90.0

    def test_u_stats_012_automation_run_linked_slot_is_included(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-078-unit-test-design.md U-STATS-012 (automation_run_id 紐付け slot も集計)"""
        run_id = _insert_automation_run(fresh_db)
        _seed_slot(
            fresh_db,
            agent_kind="codex",
            role="qa",
            automation_run_id=run_id,
            fired_at=_shifted_iso(minutes=22),
            released_at=_shifted_iso(minutes=21),
            status="completed",
        )

        rows = agent_slots.get_stats(days=7, by="agent_kind")

        assert rows[0]["total"] == 1
        assert rows[0]["completed"] == 1
