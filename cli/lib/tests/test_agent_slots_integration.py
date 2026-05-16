"""
PLAN-078 agent_slots 結合テスト (Python 層)
契約: docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §10 + PLAN-078 §4-§5
DoD 検証: docs/v2/L4-test-design/PLAN-078-integration-test-design.md
        I-LIFE-001〜I-LIFE-004 / I-FK-001〜I-FK-003 / I-STAT-001〜I-STAT-004 / I-STALE-001〜I-STALE-002
"""

from __future__ import annotations

import re
import sqlite3
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import agent_slots
import helix_db


def _sqlite_text(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _apply_sqlite_now(base_now: datetime, *args: object) -> str:
    current = base_now
    values = [str(arg).strip() for arg in args if str(arg).strip()]
    if values and values[0].lower() == "now":
        values = values[1:]
    for value in values:
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
    original_connect = agent_slots.helix_db._connect

    def _connect_with_fixed_now(db_path: str | Path):
        conn = original_connect(db_path)
        conn.create_function("datetime", -1, lambda *args: _apply_sqlite_now(base_now, *args))
        return conn

    monkeypatch.setattr(agent_slots.helix_db, "_connect", _connect_with_fixed_now)


def _instrument_lock(original_lock, hold_seconds: float = 0.1):
    state = {"active": 0, "max_active": 0, "calls": []}
    state_lock = threading.Lock()

    @contextmanager
    def wrapped(name, *args, **kwargs):
        with original_lock(name, *args, **kwargs):
            with state_lock:
                state["active"] += 1
                state["max_active"] = max(state["max_active"], state["active"])
                state["calls"].append(name)
            try:
                threading.Event().wait(hold_seconds)
                yield
            finally:
                with state_lock:
                    state["active"] -= 1

    return wrapped, state


def _seed_automation_runs(conn: sqlite3.Connection) -> None:
    rows = [
        (
            "helix-push",
            "PLAN-078",
            "system",
            _sqlite_text(datetime(2026, 5, 17, 11, 20)),
            None,
            "running",
            None,
            '{"kind":"push-1"}',
        ),
        (
            "helix-pr",
            "PLAN-078",
            "system",
            _sqlite_text(datetime(2026, 5, 17, 11, 25)),
            _sqlite_text(datetime(2026, 5, 17, 11, 30)),
            "completed",
            0,
            '{"kind":"push-2"}',
        ),
        (
            "helix-push",
            "PLAN-079",
            "system",
            _sqlite_text(datetime(2026, 5, 17, 11, 35)),
            None,
            "running",
            None,
            '{"kind":"push-3"}',
        ),
    ]
    conn.executemany(
        """
        INSERT INTO automation_runs (
            run_kind, plan_id, trigger_actor, started_at, ended_at, status, exit_code, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


@pytest.fixture
def fresh_db_with_automation_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """temp helix.db + automation_runs に seed を入れた結合テスト fixture."""
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / ".helix" / "test_agent_slots.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        _seed_automation_runs(conn)
    finally:
        conn.close()

    return {
        "db_path": db_path,
        "frozen_now": datetime(2026, 5, 17, 12, 0, 0),
        "automation_run_ids": [1, 2, 3],
    }


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
    fired_at: datetime,
    released_at: datetime | None = None,
    status: str = "running",
    exit_code: int | None = None,
    slot_source: str = "helix_codex",
) -> int:
    with helix_db._write_connection(str(db_path)) as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_slots (
                slot_key, agent_kind, role, subagent_type, plan_id, task_id, sprint,
                session_id, automation_run_id, fired_at, released_at, status, exit_code, slot_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                _sqlite_text(fired_at),
                _sqlite_text(released_at) if released_at is not None else None,
                status,
                exit_code,
                slot_source,
            ),
        )
        return int(cursor.lastrowid)


def _fetch_slot(db_path: Path, slot_id: int) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM agent_slots WHERE id = ?", (slot_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _seed_stats_dataset(db_path: Path) -> dict[str, int]:
    base = datetime(2026, 5, 17, 12, 0, 0)
    slot_ids = {
        "completed": _seed_agent_slot(
            db_path,
            agent_kind="codex",
            role="se",
            plan_id="PLAN-078",
            task_id="TASK-001",
            sprint=".4",
            session_id="sess-001",
            automation_run_id=1,
            fired_at=base - timedelta(minutes=55),
            released_at=base - timedelta(minutes=35),
            status="completed",
            exit_code=0,
        ),
        "failed": _seed_agent_slot(
            db_path,
            agent_kind="codex",
            role="qa",
            plan_id="PLAN-078",
            task_id="TASK-002",
            sprint=".4",
            session_id="sess-002",
            automation_run_id=2,
            fired_at=base - timedelta(minutes=50),
            released_at=base - timedelta(minutes=20),
            status="failed",
            exit_code=2,
        ),
        "running": _seed_agent_slot(
            db_path,
            agent_kind="claude_subagent",
            role=None,
            subagent_type="triage",
            plan_id=None,
            task_id="TASK-003",
            sprint=".4",
            session_id="sess-003",
            fired_at=base - timedelta(minutes=30),
            released_at=None,
            status="running",
            exit_code=None,
            slot_source="pretooluse_hook",
        ),
        "cancelled": _seed_agent_slot(
            db_path,
            agent_kind="claude_subagent",
            role="ops",
            subagent_type="watchdog",
            plan_id="PLAN-079",
            task_id="TASK-004",
            sprint=".4",
            session_id="sess-004",
            automation_run_id=3,
            fired_at=base - timedelta(minutes=10),
            released_at=base - timedelta(minutes=5),
            status="cancelled",
            exit_code=None,
            slot_source="pretooluse_hook",
        ),
    }
    return slot_ids


class TestFireReleaseLifecycle:
    def test_i_life_001_running_to_completed(self, fresh_db_with_automation_runs: dict[str, object]) -> None:
        """I-LIFE-001: fire → release(completed) で status と released_at を確認する。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        slot_id = agent_slots.fire_slot("codex", role="se", plan_id="PLAN-078", automation_run_id=1)

        agent_slots.release_slot(slot_id, status="completed", exit_code=0)

        row = _fetch_slot(db_path, slot_id)
        active = agent_slots.list_active_slots()

        assert row["status"] == "completed"
        assert row["released_at"] is not None
        assert row["exit_code"] == 0
        assert row["automation_run_id"] == 1
        assert all(slot["id"] != slot_id for slot in active)

    def test_i_life_002_running_to_failed(self, fresh_db_with_automation_runs: dict[str, object]) -> None:
        """I-LIFE-002: fire → release(failed) で status と exit_code を確認する。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        slot_id = agent_slots.fire_slot("codex", role="qa", plan_id="PLAN-078", automation_run_id=2)

        agent_slots.release_slot(slot_id, status="failed", exit_code=2)

        row = _fetch_slot(db_path, slot_id)
        assert row["status"] == "failed"
        assert row["released_at"] is not None
        assert row["exit_code"] == 2

    def test_i_life_003_running_to_cancelled(self, fresh_db_with_automation_runs: dict[str, object]) -> None:
        """I-LIFE-003: fire → release(cancelled) で status 遷移を確認する。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        slot_id = agent_slots.fire_slot(
            "claude_subagent",
            subagent_type="watchdog",
            plan_id="PLAN-079",
            slot_source="pretooluse_hook",
        )

        agent_slots.release_slot(slot_id, status="cancelled")

        row = _fetch_slot(db_path, slot_id)
        assert row["status"] == "cancelled"
        assert row["released_at"] is not None
        assert row["exit_code"] is None

    def test_i_life_004_double_release_is_rejected(self, fresh_db_with_automation_runs: dict[str, object]) -> None:
        """I-LIFE-004: 二重 release は sqlite3.IntegrityError で拒否されることを確認する。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        slot_id = agent_slots.fire_slot("codex", role="se", plan_id="PLAN-078")

        agent_slots.release_slot(slot_id, status="completed", exit_code=0)

        with pytest.raises(sqlite3.IntegrityError, match="slot is not running"):
            agent_slots.release_slot(slot_id, status="failed", exit_code=1)

        row = _fetch_slot(db_path, slot_id)
        assert row["status"] == "completed"
        assert row["exit_code"] == 0

    def test_i_life_005_release_without_fire_is_rejected(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-LIFE-005: 孤立 slot_id の release は ValueError で拒否されることを確認する。"""
        with pytest.raises(ValueError, match="slot_id does not exist"):
            agent_slots.release_slot(9999, status="completed", exit_code=0)


class TestAutomationRunsFK:
    def test_i_fk_001_fire_records_existing_automation_run_id(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-FK-001: 有効な automation_run_id で fire すると FK が保存される。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        slot_id = agent_slots.fire_slot("codex", role="se", automation_run_id=1)

        row = _fetch_slot(db_path, slot_id)

        assert row["automation_run_id"] == 1
        assert row["status"] == "running"

    def test_i_fk_002_fire_without_automation_run_keeps_fk_null(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-FK-002: automation_run_id 未指定の fire は NULL のまま保存される。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        slot_id = agent_slots.fire_slot("codex", role="qa")

        row = _fetch_slot(db_path, slot_id)

        assert row["automation_run_id"] is None
        assert row["status"] == "running"

    def test_i_fk_003_fire_rejects_missing_automation_run_id_when_required(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-FK-003: 存在しない automation_run_id は sqlite3.IntegrityError で拒否される。"""
        with pytest.raises(sqlite3.IntegrityError):
            agent_slots.fire_slot("codex", role="se", automation_run_id=9999)


class TestConcurrentFire:
    def test_i_fk_004_parallel_fire_is_serialized_by_lock(
        self,
        fresh_db_with_automation_runs: dict[str, object],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-FK-004: 並列 fire は file lock により直列化され、両方の slot が残る。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        original_lock = agent_slots.helix_db.file_lock
        wrapped_lock, state = _instrument_lock(original_lock, hold_seconds=0.1)
        monkeypatch.setattr(agent_slots.helix_db, "file_lock", wrapped_lock)

        barrier = threading.Barrier(2)
        errors: list[BaseException] = []
        slot_ids: list[int] = []
        slot_ids_lock = threading.Lock()

        def worker(index: int) -> None:
            try:
                barrier.wait(timeout=5)
                slot_id = agent_slots.fire_slot(
                    "codex",
                    role="se",
                    plan_id="PLAN-078",
                    automation_run_id=1,
                    session_id=f"sess-parallel-{index}",
                )
                with slot_ids_lock:
                    slot_ids.append(slot_id)
            except BaseException as exc:  # pragma: no cover - assertion path
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(index,)) for index in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert all(not thread.is_alive() for thread in threads)
        assert not errors
        assert state["calls"] == [helix_db.HELIX_DB_LOCK_NAME, helix_db.HELIX_DB_LOCK_NAME]
        assert state["max_active"] == 1
        assert len(slot_ids) == 2
        assert slot_ids[0] != slot_ids[1]

        conn = helix_db.get_connection(db_path)
        try:
            rows = conn.execute(
                "SELECT status, automation_run_id FROM agent_slots WHERE session_id LIKE 'sess-parallel-%' ORDER BY id"
            ).fetchall()
        finally:
            conn.close()

        assert len(rows) == 2
        assert all(row["status"] == "running" for row in rows)
        assert all(row["automation_run_id"] == 1 for row in rows)


class TestStatsAggregation:
    def test_i_stat_001_by_hour_aggregates_total_and_peak_parallel(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-STAT-001: 複数 slot 投入後、by=hour で件数と peak_parallel を集計できる。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        _seed_stats_dataset(db_path)

        rows = agent_slots.get_stats(days=7, by="hour")

        assert len(rows) == 1
        row = rows[0]
        assert row["total"] == 4
        assert row["running"] == 1
        assert row["completed"] == 1
        assert row["failed"] == 1
        assert row["cancelled"] == 1
        assert row["peak_parallel"] >= 2
        assert row["group"] == "2026-05-17 11:00:00"

    def test_i_stat_002_by_role_groups_none_bucket(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-STAT-002: by=role で role 別の件数が崩れず、NULL は (none) に集約される。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        _seed_stats_dataset(db_path)

        rows = agent_slots.get_stats(days=7, by="role")
        groups = {row["group"]: row for row in rows}

        assert groups["se"]["total"] == 1
        assert groups["qa"]["total"] == 1
        assert groups["ops"]["total"] == 1
        assert groups["(none)"]["total"] == 1
        assert sum(row["total"] for row in rows) == 4

    def test_i_stat_003_by_plan_id_groups_plan_specific_rows(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-STAT-003: by=plan_id で PLAN-078 / PLAN-079 / (none) が分かれて集計される。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        _seed_stats_dataset(db_path)

        rows = agent_slots.get_stats(days=7, by="plan_id")
        groups = {row["group"]: row for row in rows}

        assert groups["PLAN-078"]["total"] == 2
        assert groups["PLAN-079"]["total"] == 1
        assert groups["(none)"]["total"] == 1

    def test_i_stat_004_by_agent_kind_groups_codex_and_subagent(
        self,
        fresh_db_with_automation_runs: dict[str, object],
    ) -> None:
        """I-STAT-004: by=agent_kind で codex と claude_subagent が別グループになる。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        _seed_stats_dataset(db_path)

        rows = agent_slots.get_stats(days=7, by="agent_kind")
        groups = {row["group"]: row for row in rows}

        assert groups["codex"]["total"] == 2
        assert groups["claude_subagent"]["total"] == 2
        assert sum(row["total"] for row in rows) == 4


class TestStaleDetection:
    def test_i_stale_001_under_threshold_excludes_recent_running_slot(
        self,
        fresh_db_with_automation_runs: dict[str, object],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-STALE-001: 4分59秒相当の running slot は stale に含まれない。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        _patch_sqlite_now(monkeypatch, fresh_db_with_automation_runs["frozen_now"])
        _seed_agent_slot(
            db_path,
            agent_kind="codex",
            role="se",
            plan_id="PLAN-078",
            fired_at=fresh_db_with_automation_runs["frozen_now"] - timedelta(minutes=4, seconds=59),
            released_at=None,
            status="running",
            exit_code=None,
        )

        rows = agent_slots.list_stale_slots(threshold_minutes=5)

        assert rows == []

    def test_i_stale_002_threshold_boundary_includes_exact_five_minutes(
        self,
        fresh_db_with_automation_runs: dict[str, object],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """I-STALE-002: ちょうど 5分00秒の running slot は stale に含まれる。"""
        db_path = fresh_db_with_automation_runs["db_path"]
        _patch_sqlite_now(monkeypatch, fresh_db_with_automation_runs["frozen_now"])
        slot_id = _seed_agent_slot(
            db_path,
            agent_kind="claude_subagent",
            role=None,
            subagent_type="watchdog",
            plan_id="PLAN-079",
            fired_at=fresh_db_with_automation_runs["frozen_now"] - timedelta(minutes=5),
            released_at=None,
            status="running",
            exit_code=None,
            slot_source="pretooluse_hook",
        )

        rows = agent_slots.list_stale_slots(threshold_minutes=5)

        assert [row["id"] for row in rows] == [slot_id]
        assert rows[0]["status"] == "running"
