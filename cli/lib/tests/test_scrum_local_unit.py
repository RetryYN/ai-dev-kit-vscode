"""PLAN-079 scrum_local 単体テスト.

契約: docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §11
DoD 検証: docs/v2/L4-test-design/PLAN-079-unit-test-design.md U-SL-INIT-001〜U-SL-STATS-006
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import scrum_local


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _ts(*, days: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    return (_utc_now() - timedelta(days=days, minutes=minutes, seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")


def _ts_future(*, seconds: int = 1) -> str:
    return (_utc_now() + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")


def _open_conn(db_path: Path) -> sqlite3.Connection:
    conn = helix_db.get_connection(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _seed_fresh_db(db_path: Path) -> None:
    with helix_db._write_connection(str(db_path), ensure_schema=False) as conn:
        conn.executescript(helix_db.SCHEMA)
        conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
        helix_db.migrate_all(conn)


def _fetch_scrum_loop(db_path: Path, loop_id: str) -> sqlite3.Row:
    conn = _open_conn(db_path)
    try:
        row = conn.execute("SELECT * FROM scrum_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _fetch_latest_audit_payload(db_path: Path) -> dict:
    conn = _open_conn(db_path)
    try:
        row = conn.execute(
            "SELECT payload FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return json.loads(row["payload"])


def _insert_agent_slot(
    db_path: Path,
    *,
    slot_key: str = "codex:tl",
    agent_kind: str = "codex",
    role: str = "tl",
    status: str = "running",
    fired_at: str | None = None,
) -> int:
    payload = {
        "slot_key": slot_key,
        "agent_kind": agent_kind,
        "role": role,
        "subagent_type": None,
        "plan_id": None,
        "task_id": None,
        "sprint": None,
        "session_id": None,
        "automation_run_id": None,
        "fired_at": fired_at or _ts(minutes=1),
        "released_at": None,
        "status": status,
        "exit_code": None,
        "slot_source": "helix_codex",
    }
    columns = list(payload)
    placeholders = ", ".join(["?"] * len(columns))
    with helix_db._write_connection(str(db_path)) as conn:
        cursor = conn.execute(
            f"INSERT INTO agent_slots ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )
        return int(cursor.lastrowid)


def _insert_scrum_loop(
    db_path: Path,
    *,
    loop_id: str,
    forward_layer: str = "L4",
    forward_plan_id: str | None = None,
    hypothesis: str = "hypothesis",
    acceptance: str = "acceptance",
    state: str = "S0",
    decide_result: str | None = None,
    started_at: str | None = None,
    decided_at: str | None = None,
    parent_loop_id: str | None = None,
    related_agent_slot_id: int | None = None,
) -> None:
    payload = {
        "loop_id": loop_id,
        "forward_layer": forward_layer,
        "forward_plan_id": forward_plan_id,
        "hypothesis": hypothesis,
        "acceptance": acceptance,
        "state": state,
        "decide_result": decide_result,
        "started_at": started_at or _ts(minutes=10),
        "decided_at": decided_at,
        "parent_loop_id": parent_loop_id,
        "related_agent_slot_id": related_agent_slot_id,
        "created_at": _ts(minutes=10),
    }
    columns = list(payload)
    placeholders = ", ".join(["?"] * len(columns))
    with helix_db._write_connection(str(db_path)) as conn:
        conn.execute(
            f"INSERT INTO scrum_local_loops ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """fresh SQLite を作成し、HELIX_DB_PATH を temp DB に固定する。"""
    db_path = tmp_path / "test_helix.db"
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    _seed_fresh_db(db_path)
    return db_path


class TestInitLocalLoop:
    def test_u_sl_init_001_creates_first_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-001 (初回 loop は H-LOCAL-001 を返す)"""
        loop_id = scrum_local.init_local_loop("L4", "solve the pocket", "record the decision")

        row = _fetch_scrum_loop(fresh_db, loop_id)
        assert loop_id == "H-LOCAL-001"
        assert row["forward_layer"] == "L4"
        assert row["hypothesis"] == "solve the pocket"
        assert row["acceptance"] == "record the decision"
        assert row["state"] == "S0"

    def test_u_sl_init_002_persists_forward_plan_id(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-002 (forward_plan_id を保存)"""
        loop_id = scrum_local.init_local_loop(
            "L4",
            "validate the chain",
            "link the plan",
            forward_plan_id="PLAN-079",
        )

        row = _fetch_scrum_loop(fresh_db, loop_id)
        assert row["forward_plan_id"] == "PLAN-079"

    def test_u_sl_init_003_allows_parent_loop_reference(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-003 (既存 parent_loop_id を trace する)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-100", state="S3", decide_result="confirmed")

        loop_id = scrum_local.init_local_loop(
            "L4",
            "child loop",
            "child acceptance",
            parent_loop_id="H-LOCAL-100",
        )

        row = _fetch_scrum_loop(fresh_db, loop_id)
        assert row["parent_loop_id"] == "H-LOCAL-100"
        assert loop_id == "H-LOCAL-101"

    def test_u_sl_init_004_rejects_missing_parent_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-004 (存在しない parent_loop_id は拒否)"""
        with pytest.raises(ValueError, match="loop_id does not exist"):
            scrum_local.init_local_loop(
                "L4",
                "child loop",
                "child acceptance",
                parent_loop_id="H-LOCAL-999",
            )

    def test_u_sl_init_005_rejects_invalid_forward_layer(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-005 (forward_layer=LX は ValueError)"""
        with pytest.raises(ValueError, match="invalid forward_layer"):
            scrum_local.init_local_loop("LX", "hypothesis", "acceptance")

    def test_u_sl_init_006_rejects_empty_forward_layer(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-006 (forward_layer 空文字は ValueError)"""
        with pytest.raises(ValueError, match="forward_layer must be non-empty"):
            scrum_local.init_local_loop("  ", "hypothesis", "acceptance")

    def test_u_sl_init_007_rejects_empty_hypothesis(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-007 (hypothesis 空文字は ValueError)"""
        with pytest.raises(ValueError, match="hypothesis must be non-empty"):
            scrum_local.init_local_loop("L4", "  ", "acceptance")

    def test_u_sl_init_008_rejects_empty_acceptance(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-INIT-008 (acceptance 空文字は ValueError)"""
        with pytest.raises(ValueError, match="acceptance must be non-empty"):
            scrum_local.init_local_loop("L4", "hypothesis", "   ")


class TestRecordPoc:
    def test_u_sl_poc_001_transitions_s0_to_s1(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-POC-001 (S0 loop は S1 に進む)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-200")

        scrum_local.record_poc("H-LOCAL-200", commit_sha="abc123")

        row = _fetch_scrum_loop(fresh_db, "H-LOCAL-200")
        assert row["state"] == "S1"

    def test_u_sl_poc_002_persists_commit_sha_in_audit_log(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-POC-002 (commit_sha を audit_log に残す)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-201")

        scrum_local.record_poc("H-LOCAL-201", commit_sha="deadbeef")

        payload = _fetch_latest_audit_payload(fresh_db)
        assert payload["action"] == "record_poc"
        assert payload["commit_sha"] == "deadbeef"
        assert payload["loop_id"] == "H-LOCAL-201"

    def test_u_sl_poc_003_persists_agent_slot_id(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-POC-003 (agent_slot_id を関連付ける)"""
        slot_id = _insert_agent_slot(fresh_db)
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-202")

        scrum_local.record_poc("H-LOCAL-202", agent_slot_id=slot_id)

        row = _fetch_scrum_loop(fresh_db, "H-LOCAL-202")
        assert row["related_agent_slot_id"] == slot_id

    def test_u_sl_poc_004_rejects_missing_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-POC-004 (loop_id 不在は ValueError)"""
        with pytest.raises(ValueError, match="loop_id does not exist"):
            scrum_local.record_poc("H-LOCAL-404", commit_sha="abc123")

    def test_u_sl_poc_005_rejects_wrong_state(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-POC-005 (S1 loop は record_poc できない)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-203", state="S1")

        with pytest.raises(ValueError, match="loop state must be S0"):
            scrum_local.record_poc("H-LOCAL-203", commit_sha="abc123")

    def test_u_sl_poc_006_rejects_invalid_agent_slot_fk(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-POC-006 (関連 slot の FK 不整合は IntegrityError)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-204")

        with pytest.raises(sqlite3.IntegrityError):
            scrum_local.record_poc("H-LOCAL-204", agent_slot_id=99999)


class TestVerifyLoop:
    def test_u_sl_verify_001_transitions_s1_to_s2(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-VERIFY-001 (S1 loop は S2 に進む)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-300", state="S1")

        scrum_local.verify_loop("H-LOCAL-300", observation="verified")

        row = _fetch_scrum_loop(fresh_db, "H-LOCAL-300")
        assert row["state"] == "S2"

    def test_u_sl_verify_002_persists_observation_in_audit_log(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-VERIFY-002 (observation を audit_log に残す)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-301", state="S1")

        scrum_local.verify_loop("H-LOCAL-301", observation="checked")

        payload = _fetch_latest_audit_payload(fresh_db)
        assert payload["action"] == "verify_loop"
        assert payload["observation"] == "checked"

    def test_u_sl_verify_003_normalizes_empty_observation_to_null(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-VERIFY-003 (空 observation は NULL 扱い)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-302", state="S1")

        scrum_local.verify_loop("H-LOCAL-302", observation="   ")

        payload = _fetch_latest_audit_payload(fresh_db)
        assert payload["observation"] is None

    def test_u_sl_verify_004_rejects_missing_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-VERIFY-004 (loop_id 不在は ValueError)"""
        with pytest.raises(ValueError, match="loop_id does not exist"):
            scrum_local.verify_loop("H-LOCAL-404", observation="checked")

    def test_u_sl_verify_005_rejects_state_s0(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-VERIFY-005 (S0 loop は verify できない)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-303", state="S0")

        with pytest.raises(ValueError, match="loop state must be S1"):
            scrum_local.verify_loop("H-LOCAL-303", observation="checked")

    def test_u_sl_verify_006_rejects_state_s2(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-VERIFY-006 (S2 loop の再 verify は拒否)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-304", state="S2")

        with pytest.raises(ValueError, match="loop state must be S1"):
            scrum_local.verify_loop("H-LOCAL-304", observation="checked")


class TestDecideLoop:
    def test_u_sl_decide_001_confirms_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-001 (confirmed で S3 に進む)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-400", state="S2")

        scrum_local.decide_loop("H-LOCAL-400", "confirmed", note="approved")

        row = _fetch_scrum_loop(fresh_db, "H-LOCAL-400")
        assert row["state"] == "S3"
        assert row["decide_result"] == "confirmed"
        assert row["decided_at"] is not None

    def test_u_sl_decide_002_rejects_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-002 (rejected でも S3 に進む)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-401", state="S2")

        scrum_local.decide_loop("H-LOCAL-401", "rejected")

        row = _fetch_scrum_loop(fresh_db, "H-LOCAL-401")
        assert row["decide_result"] == "rejected"
        assert row["state"] == "S3"

    def test_u_sl_decide_003_records_pivot_result(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-003 (pivot を保存)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-402", state="S2")

        scrum_local.decide_loop("H-LOCAL-402", "pivot")

        row = _fetch_scrum_loop(fresh_db, "H-LOCAL-402")
        assert row["decide_result"] == "pivot"

    def test_u_sl_decide_004_persists_note_in_audit_log(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-004 (note を audit_log に残す)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-403", state="S2")

        scrum_local.decide_loop("H-LOCAL-403", "confirmed", note="final note")

        payload = _fetch_latest_audit_payload(fresh_db)
        assert payload["action"] == "decide_loop"
        assert payload["note"] == "final note"

    def test_u_sl_decide_005_rejects_empty_result(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-005 (result 空文字は ValueError)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-404", state="S2")

        with pytest.raises(ValueError, match="result must be non-empty"):
            scrum_local.decide_loop("H-LOCAL-404", "   ")

    def test_u_sl_decide_006_rejects_unknown_result(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-006 (unknown result は ValueError)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-405", state="S2")

        with pytest.raises(ValueError, match="invalid result"):
            scrum_local.decide_loop("H-LOCAL-405", "unknown")

    def test_u_sl_decide_007_rejects_non_s2_state(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-007 (S1 loop は decide できない)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-406", state="S1")

        with pytest.raises(ValueError, match="loop state must be S2"):
            scrum_local.decide_loop("H-LOCAL-406", "confirmed")

    def test_u_sl_decide_008_rejects_terminal_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-DECIDE-008 (S3 loop の再 decide は拒否)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-407", state="S3", decide_result="confirmed")

        with pytest.raises(ValueError, match="loop state must be S2"):
            scrum_local.decide_loop("H-LOCAL-407", "confirmed")


class TestListActiveLoops:
    def test_u_sl_list_001_excludes_decided_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-LIST-001 (S3 rows を除外)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-500", state="S3", decide_result="confirmed")
        active_id = "H-LOCAL-501"
        _insert_scrum_loop(fresh_db, loop_id=active_id, state="S2")

        rows = scrum_local.list_active_loops()

        assert [row["loop_id"] for row in rows] == [active_id]

    def test_u_sl_list_002_returns_empty_list_when_no_active_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-LIST-002 (active がなければ空 list)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-502", state="S3", decide_result="confirmed")

        assert scrum_local.list_active_loops() == []

    def test_u_sl_list_003_returns_all_active_rows_without_filter(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-LIST-003 (forward_layer 未指定で全 active を返す)"""
        first = "H-LOCAL-503"
        second = "H-LOCAL-504"
        _insert_scrum_loop(fresh_db, loop_id=first, forward_layer="L4", state="S1")
        _insert_scrum_loop(fresh_db, loop_id=second, forward_layer="L5", state="S2")

        rows = scrum_local.list_active_loops()

        assert {row["loop_id"] for row in rows} == {first, second}

    def test_u_sl_list_004_filters_by_forward_layer(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-LIST-004 (forward_layer で絞り込む)"""
        first = "H-LOCAL-505"
        second = "H-LOCAL-506"
        _insert_scrum_loop(fresh_db, loop_id=first, forward_layer="L4", state="S1")
        _insert_scrum_loop(fresh_db, loop_id=second, forward_layer="L5", state="S1")

        rows = scrum_local.list_active_loops("L4")

        assert [row["loop_id"] for row in rows] == [first]

    def test_u_sl_list_005_preserves_row_shape(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-LIST-005 (主要列を含む dict を返す)"""
        loop_id = "H-LOCAL-507"
        _insert_scrum_loop(
            fresh_db,
            loop_id=loop_id,
            forward_layer="L6",
            forward_plan_id="PLAN-079",
            parent_loop_id=None,
            state="S1",
        )

        row = scrum_local.list_active_loops()[0]

        assert row["loop_id"] == loop_id
        assert {"loop_id", "forward_layer", "forward_plan_id", "hypothesis", "acceptance", "state", "decide_result", "started_at", "decided_at", "parent_loop_id", "related_agent_slot_id", "created_at"} <= set(row.keys())

    def test_u_sl_list_006_orders_by_started_at_then_loop_id(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-LIST-006 (started_at / loop_id の順序を維持)"""
        older = "H-LOCAL-508"
        newer = "H-LOCAL-509"
        _insert_scrum_loop(fresh_db, loop_id=older, state="S1", started_at=_ts(minutes=20))
        _insert_scrum_loop(fresh_db, loop_id=newer, state="S1", started_at=_ts(minutes=10))

        rows = scrum_local.list_active_loops()

        assert [row["loop_id"] for row in rows] == [older, newer]


class TestGetStats:
    def test_u_sl_stats_001_counts_decide_results(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-STATS-001 (confirmed/rejected/pivot を集計)"""
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-600",
            state="S3",
            decide_result="confirmed",
            decided_at=_ts(minutes=30),
        )
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-601",
            state="S3",
            decide_result="rejected",
            decided_at=_ts(minutes=20),
        )
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-602",
            state="S3",
            decide_result="pivot",
            decided_at=_ts(minutes=10),
        )

        stats = scrum_local.get_stats()

        assert stats == {"confirmed": 1, "rejected": 1, "pivot": 1, "total": 3}

    def test_u_sl_stats_002_respects_days_window(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-STATS-002 (days=1 で古い row を除外)"""
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-603",
            state="S3",
            decide_result="confirmed",
            decided_at=_ts(minutes=5),
        )
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-604",
            state="S3",
            decide_result="rejected",
            decided_at=_ts(days=2),
        )

        stats = scrum_local.get_stats(days=1)

        assert stats == {"confirmed": 1, "rejected": 0, "pivot": 0, "total": 1}

    def test_u_sl_stats_003_includes_future_dated_rows_for_zero_days(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-STATS-003 (days=0 は現在以後の row を含む)"""
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-605",
            state="S3",
            decide_result="confirmed",
            decided_at=_ts_future(seconds=1),
        )

        stats = scrum_local.get_stats(days=0)

        assert stats == {"confirmed": 1, "rejected": 0, "pivot": 0, "total": 1}

    def test_u_sl_stats_004_rejects_negative_days(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-STATS-004 (days=-1 は ValueError)"""
        with pytest.raises(ValueError, match="days must be a non-negative integer"):
            scrum_local.get_stats(days=-1)

    def test_u_sl_stats_005_ignores_running_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-STATS-005 (decide_result NULL の running row を除外)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-606", state="S1", decide_result=None, decided_at=None)

        stats = scrum_local.get_stats()

        assert stats == {"confirmed": 0, "rejected": 0, "pivot": 0, "total": 0}

    def test_u_sl_stats_006_handles_mixed_layers_without_breaking_totals(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-SL-STATS-006 (layer が混在しても total は崩れない)"""
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-607",
            forward_layer="L4",
            state="S3",
            decide_result="confirmed",
            decided_at=_ts(minutes=3),
        )
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-608",
            forward_layer="L5",
            state="S3",
            decide_result="confirmed",
            decided_at=_ts(minutes=2),
        )

        stats = scrum_local.get_stats()

        assert stats["confirmed"] == 2
        assert stats["total"] == 2
