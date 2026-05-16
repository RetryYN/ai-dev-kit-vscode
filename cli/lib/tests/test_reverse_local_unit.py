"""PLAN-079 reverse_local 単体テスト.

契約: docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §12
DoD 検証: docs/v2/L4-test-design/PLAN-079-unit-test-design.md U-RL-INIT-001〜U-RL-STATS-004
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
import reverse_local


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


def _fetch_reverse_loop(db_path: Path, loop_id: str) -> sqlite3.Row:
    conn = _open_conn(db_path)
    try:
        row = conn.execute("SELECT * FROM reverse_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
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


def _insert_scrum_loop(
    db_path: Path,
    *,
    loop_id: str,
    forward_layer: str = "L4",
    state: str = "S3",
    decide_result: str = "confirmed",
    parent_loop_id: str | None = None,
    decided_at: str | None = None,
    started_at: str | None = None,
) -> None:
    payload = {
        "loop_id": loop_id,
        "forward_layer": forward_layer,
        "forward_plan_id": "PLAN-079" if forward_layer else None,
        "hypothesis": "hypothesis",
        "acceptance": "acceptance",
        "state": state,
        "decide_result": decide_result,
        "started_at": started_at or _ts(minutes=30),
        "decided_at": decided_at or _ts(minutes=20),
        "parent_loop_id": parent_loop_id,
        "related_agent_slot_id": None,
        "created_at": _ts(minutes=30),
    }
    columns = list(payload)
    placeholders = ", ".join(["?"] * len(columns))
    with helix_db._write_connection(str(db_path)) as conn:
        conn.execute(
            f"INSERT INTO scrum_local_loops ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )


def _insert_reverse_loop(
    db_path: Path,
    *,
    loop_id: str,
    parent_scrum_loop_id: str,
    reverse_type: str = "scrum-to-forward",
    state: str = "R0",
    target_forward_plan: str | None = None,
    target_forward_layer: str | None = None,
    artifact_links: str | None = None,
    started_at: str | None = None,
    routed_at: str | None = None,
) -> None:
    conn = _open_conn(db_path)
    try:
        parent_exists = conn.execute(
            "SELECT 1 FROM scrum_local_loops WHERE loop_id = ?",
            (parent_scrum_loop_id,),
        ).fetchone()
    finally:
        conn.close()
    if parent_exists is None:
        _insert_scrum_loop(db_path, loop_id=parent_scrum_loop_id, state="S3", decide_result="confirmed")

    payload = {
        "loop_id": loop_id,
        "parent_scrum_loop_id": parent_scrum_loop_id,
        "reverse_type": reverse_type,
        "state": state,
        "target_forward_plan": target_forward_plan,
        "target_forward_layer": target_forward_layer,
        "started_at": started_at or _ts(minutes=20),
        "routed_at": routed_at,
        "artifact_links": artifact_links,
        "created_at": _ts(minutes=20),
    }
    columns = list(payload)
    placeholders = ", ".join(["?"] * len(columns))
    with helix_db._write_connection(str(db_path)) as conn:
        conn.execute(
            f"INSERT INTO reverse_local_loops ({', '.join(columns)}) VALUES ({placeholders})",
            [payload[column] for column in columns],
        )


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """fresh SQLite を作成し、HELIX_DB_PATH を temp DB に固定する。"""
    db_path = tmp_path / "test_helix.db"
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    _seed_fresh_db(db_path)
    return db_path


class TestInitFromScrum:
    def test_u_rl_init_001_creates_reverse_loop_from_confirmed_scrum(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-INIT-001 (confirmed scrum から RL-001 を作成)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-900", state="S3", decide_result="confirmed")

        loop_id = reverse_local.init_from_scrum("H-LOCAL-900")

        row = _fetch_reverse_loop(fresh_db, loop_id)
        assert loop_id == "RL-001"
        assert row["parent_scrum_loop_id"] == "H-LOCAL-900"
        assert row["reverse_type"] == "scrum-to-forward"
        assert row["state"] == "R0"

    def test_u_rl_init_002_persists_default_reverse_type(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-INIT-002 (既定 reverse_type を保存)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-901", state="S3", decide_result="confirmed")

        loop_id = reverse_local.init_from_scrum("H-LOCAL-901")

        row = _fetch_reverse_loop(fresh_db, loop_id)
        assert row["reverse_type"] == "scrum-to-forward"

    def test_u_rl_init_003_rejects_missing_scrum_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-INIT-003 (存在しない scrum_loop_id は ValueError)"""
        with pytest.raises(ValueError, match="confirmed scrum loop does not exist"):
            reverse_local.init_from_scrum("H-LOCAL-999")

    def test_u_rl_init_004_rejects_unconfirmed_scrum_loop(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-INIT-004 (未 confirmed の scrum は拒否)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-902", state="S2", decide_result="rejected")

        with pytest.raises(ValueError, match="confirmed scrum loop does not exist"):
            reverse_local.init_from_scrum("H-LOCAL-902")

    def test_u_rl_init_005_keeps_source_trace_when_scrum_has_parent(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-INIT-005 (source scrum の parent trace を壊さない)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-100", state="S3", decide_result="confirmed")
        _insert_scrum_loop(
            fresh_db,
            loop_id="H-LOCAL-903",
            state="S3",
            decide_result="confirmed",
            parent_loop_id="H-LOCAL-100",
        )

        loop_id = reverse_local.init_from_scrum("H-LOCAL-903")

        row = _fetch_reverse_loop(fresh_db, loop_id)
        assert row["parent_scrum_loop_id"] == "H-LOCAL-903"

    def test_u_rl_init_006_rejects_empty_reverse_type(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-INIT-006 (reverse_type 空文字は ValueError)"""
        _insert_scrum_loop(fresh_db, loop_id="H-LOCAL-904", state="S3", decide_result="confirmed")

        with pytest.raises(ValueError, match="reverse_type must be non-empty"):
            reverse_local.init_from_scrum("H-LOCAL-904", reverse_type="   ")


class TestTransitionState:
    def test_u_rl_trans_001_transitions_r0_to_r1(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-001 (R0 -> R1 を許可)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-100", parent_scrum_loop_id="H-LOCAL-910", state="R0")

        reverse_local.transition_state("RL-100", "R1")

        row = _fetch_reverse_loop(fresh_db, "RL-100")
        assert row["state"] == "R1"

    def test_u_rl_trans_002_transitions_r1_to_r2(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-002 (R1 -> R2 を許可)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-101", parent_scrum_loop_id="H-LOCAL-911", state="R1")

        reverse_local.transition_state("RL-101", "R2")

        row = _fetch_reverse_loop(fresh_db, "RL-101")
        assert row["state"] == "R2"

    def test_u_rl_trans_003_transitions_r2_to_r3(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-003 (R2 -> R3 を許可)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-102", parent_scrum_loop_id="H-LOCAL-912", state="R2")

        reverse_local.transition_state("RL-102", "R3")

        row = _fetch_reverse_loop(fresh_db, "RL-102")
        assert row["state"] == "R3"

    def test_u_rl_trans_004_transitions_r3_to_r4(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-004 (R3 -> R4 を許可)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-103", parent_scrum_loop_id="H-LOCAL-913", state="R3")

        reverse_local.transition_state("RL-103", "R4")

        row = _fetch_reverse_loop(fresh_db, "RL-103")
        assert row["state"] == "R4"

    def test_u_rl_trans_005_rejects_skip_transition(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-005 (R0 -> R2 の skip は拒否)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-104", parent_scrum_loop_id="H-LOCAL-914", state="R0")

        with pytest.raises(ValueError, match="invalid state transition"):
            reverse_local.transition_state("RL-104", "R2")

    def test_u_rl_trans_006_rejects_rewind_from_terminal_state(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-006 (R4 -> R1 の巻戻しは拒否)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-105", parent_scrum_loop_id="H-LOCAL-915", state="R4")

        with pytest.raises(ValueError, match="invalid state transition"):
            reverse_local.transition_state("RL-105", "R1")

    def test_u_rl_trans_007_rejects_empty_new_state(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-007 (new_state 空文字は ValueError)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-106", parent_scrum_loop_id="H-LOCAL-916", state="R0")

        with pytest.raises(ValueError, match="new_state must be non-empty"):
            reverse_local.transition_state("RL-106", "   ")

    def test_u_rl_trans_008_rejects_invalid_new_state(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-TRANS-008 (new_state=RX は ValueError)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-107", parent_scrum_loop_id="H-LOCAL-917", state="R0")

        with pytest.raises(ValueError, match="invalid new_state"):
            reverse_local.transition_state("RL-107", "RX")


class TestRouteToForward:
    def test_u_rl_route_001_saves_target_plan_and_layer(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-ROUTE-001 (target_plan と target_layer を保存)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-200", parent_scrum_loop_id="H-LOCAL-920", state="R4")

        reverse_local.route_to_forward("RL-200", "PLAN-079", "L4")

        row = _fetch_reverse_loop(fresh_db, "RL-200")
        assert row["target_forward_plan"] == "PLAN-079"
        assert row["target_forward_layer"] == "L4"
        assert row["routed_at"] is not None

    def test_u_rl_route_002_serializes_artifact_links(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-ROUTE-002 (artifact_links を JSON 保存)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-201", parent_scrum_loop_id="H-LOCAL-921", state="R4")

        links = [{"kind": "covers", "ref": "docs/v2/L4-test-design/PLAN-079-unit-test-design.md"}]
        reverse_local.route_to_forward("RL-201", "PLAN-079", "L3", artifact_links=links)

        row = _fetch_reverse_loop(fresh_db, "RL-201")
        assert json.loads(row["artifact_links"]) == links

    def test_u_rl_route_003_accepts_lower_layers(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-ROUTE-003 (L1 を許可)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-202", parent_scrum_loop_id="H-LOCAL-922", state="R4")

        reverse_local.route_to_forward("RL-202", "PLAN-079", "L1")

        row = _fetch_reverse_loop(fresh_db, "RL-202")
        assert row["target_forward_layer"] == "L1"

    def test_u_rl_route_004_accepts_upper_allowed_layer(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-ROUTE-004 (L4 を許可)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-203", parent_scrum_loop_id="H-LOCAL-923", state="R4")

        reverse_local.route_to_forward("RL-203", "PLAN-079", "L4")

        row = _fetch_reverse_loop(fresh_db, "RL-203")
        assert row["target_forward_layer"] == "L4"

    def test_u_rl_route_005_rejects_invalid_target_layer(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-ROUTE-005 (target_layer=L5 は ValueError)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-204", parent_scrum_loop_id="H-LOCAL-924", state="R4")

        with pytest.raises(ValueError, match="invalid target_layer"):
            reverse_local.route_to_forward("RL-204", "PLAN-079", "L5")

    def test_u_rl_route_006_rejects_empty_target_plan(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-ROUTE-006 (target_plan 空文字は ValueError)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-205", parent_scrum_loop_id="H-LOCAL-925", state="R4")

        with pytest.raises(ValueError, match="target_plan must be non-empty"):
            reverse_local.route_to_forward("RL-205", "   ", "L4")


class TestListActiveLoops:
    def test_u_rl_list_001_excludes_r4_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-LIST-001 (R4 row を除外)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-300", parent_scrum_loop_id="H-LOCAL-930", state="R4")
        active_id = "RL-301"
        _insert_reverse_loop(fresh_db, loop_id=active_id, parent_scrum_loop_id="H-LOCAL-931", state="R2")

        rows = reverse_local.list_active_loops()

        assert [row["loop_id"] for row in rows] == [active_id]

    def test_u_rl_list_002_returns_empty_list_when_no_active_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-LIST-002 (active がなければ空 list)"""
        _insert_reverse_loop(fresh_db, loop_id="RL-302", parent_scrum_loop_id="H-LOCAL-932", state="R4")

        assert reverse_local.list_active_loops() == []

    def test_u_rl_list_003_returns_all_active_rows(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-LIST-003 (filter 無しで全 active を返す)"""
        first = "RL-303"
        second = "RL-304"
        _insert_reverse_loop(fresh_db, loop_id=first, parent_scrum_loop_id="H-LOCAL-933", state="R0")
        _insert_reverse_loop(fresh_db, loop_id=second, parent_scrum_loop_id="H-LOCAL-934", state="R3")

        rows = reverse_local.list_active_loops()

        assert {row["loop_id"] for row in rows} == {first, second}

    def test_u_rl_list_004_preserves_row_shape(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-LIST-004 (主要列を持つ dict を返す)"""
        loop_id = "RL-305"
        _insert_reverse_loop(
            fresh_db,
            loop_id=loop_id,
            parent_scrum_loop_id="H-LOCAL-935",
            state="R1",
            target_forward_plan="PLAN-079",
            target_forward_layer="L4",
        )

        row = reverse_local.list_active_loops()[0]

        assert row["loop_id"] == loop_id
        assert {"loop_id", "parent_scrum_loop_id", "reverse_type", "state", "target_forward_plan", "target_forward_layer", "started_at", "routed_at", "artifact_links", "created_at"} <= set(row.keys())


class TestGetRoutingStats:
    def test_u_rl_stats_001_counts_layers(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-STATS-001 (layer 別を集計)"""
        _insert_reverse_loop(
            fresh_db,
            loop_id="RL-400",
            parent_scrum_loop_id="H-LOCAL-940",
            state="R4",
            target_forward_plan="PLAN-079",
            target_forward_layer="L1",
            routed_at=_ts(minutes=10),
        )
        _insert_reverse_loop(
            fresh_db,
            loop_id="RL-401",
            parent_scrum_loop_id="H-LOCAL-941",
            state="R4",
            target_forward_plan="PLAN-079",
            target_forward_layer="L4",
            routed_at=_ts(minutes=5),
        )

        stats = reverse_local.get_routing_stats()

        assert stats == {"layers": {"L1": 1, "L4": 1}, "total": 2}

    def test_u_rl_stats_002_respects_days_window(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-STATS-002 (days=1 で古い row を除外)"""
        _insert_reverse_loop(
            fresh_db,
            loop_id="RL-402",
            parent_scrum_loop_id="H-LOCAL-942",
            state="R4",
            target_forward_plan="PLAN-079",
            target_forward_layer="L2",
            routed_at=_ts(minutes=5),
        )
        _insert_reverse_loop(
            fresh_db,
            loop_id="RL-403",
            parent_scrum_loop_id="H-LOCAL-943",
            state="R4",
            target_forward_plan="PLAN-079",
            target_forward_layer="L2",
            routed_at=_ts(days=2),
        )

        stats = reverse_local.get_routing_stats(days=1)

        assert stats == {"layers": {"L2": 1}, "total": 1}

    def test_u_rl_stats_003_includes_future_dated_rows_for_zero_days(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-STATS-003 (days=0 は現在以後の row を含む)"""
        _insert_reverse_loop(
            fresh_db,
            loop_id="RL-404",
            parent_scrum_loop_id="H-LOCAL-944",
            state="R4",
            target_forward_plan="PLAN-079",
            target_forward_layer="L3",
            routed_at=_ts_future(seconds=1),
        )

        stats = reverse_local.get_routing_stats(days=0)

        assert stats == {"layers": {"L3": 1}, "total": 1}

    def test_u_rl_stats_004_rejects_negative_days(self, fresh_db: Path) -> None:
        """DoD 検証: PLAN-079-unit-test-design.md U-RL-STATS-004 (days=-1 は ValueError)"""
        with pytest.raises(ValueError, match="days must be a non-negative integer"):
            reverse_local.get_routing_stats(days=-1)
