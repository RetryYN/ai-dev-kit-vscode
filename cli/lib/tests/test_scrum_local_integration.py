"""DoD 検証: PLAN-079-integration-test-design.md
対象実装: cli/lib/scrum_local.py
結合テスト範囲:
  - I-UPS-LIFE-001 / I-UPS-LIFE-002 / I-UPS-LIFE-003 / I-UPS-LIFE-005 / I-UPS-LIFE-006
  - I-FK-001 / I-FK-003
  - I-PIVOT-001 / I-PIVOT-002
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import agent_slots
import helix_db
import scrum_local


def _fetch_scrum_loop(db_path: Path, loop_id: str) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM scrum_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _fetch_agent_slot(db_path: Path, slot_id: int) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM agent_slots WHERE id = ?", (slot_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _fetch_automation_run(db_path: Path, run_id: int) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id, plan_id, trigger_actor, status FROM automation_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)
    return db_path


def _seed_automation_run(db_path: Path, plan_id: str = "PLAN-079") -> int:
    with helix_db._write_connection(str(db_path)) as conn:
        return helix_db.insert_automation_run(
            conn,
            trigger_source="test",
            run_kind="push",
            metadata={"plan_id": plan_id, "source": "scrum-local-integration"},
        )


def _seed_agent_slot(
    db_path: Path,
    *,
    plan_id: str = "PLAN-079",
    automation_run_id: int | None = None,
) -> int:
    return agent_slots.fire_slot(
        agent_kind="codex",
        role="se",
        plan_id=plan_id,
        automation_run_id=automation_run_id,
    )


def _seed_running_loop(
    db_path: Path,
    *,
    forward_layer: str = "L4",
    forward_plan_id: str = "PLAN-079",
    hypothesis: str = "wrap smoke",
    acceptance: str = "local loop created",
    parent_loop_id: str | None = None,
) -> str:
    loop_id = scrum_local.init_local_loop(
        forward_layer=forward_layer,
        forward_plan_id=forward_plan_id,
        hypothesis=hypothesis,
        acceptance=acceptance,
        parent_loop_id=parent_loop_id,
    )
    row = _fetch_scrum_loop(db_path, loop_id)
    assert row["state"] == "S0"
    assert row["forward_layer"] == forward_layer
    return loop_id


def _seed_verified_loop(
    db_path: Path,
    *,
    result: str = "confirmed",
    parent_loop_id: str | None = None,
    slot_id: int | None = None,
) -> str:
    loop_id = _seed_running_loop(db_path, parent_loop_id=parent_loop_id)
    scrum_local.record_poc(loop_id, commit_sha="abc1234", agent_slot_id=slot_id)
    scrum_local.verify_loop(loop_id, observation="checked locally")
    scrum_local.decide_loop(loop_id, result=result, note=f"decision={result}")
    row = _fetch_scrum_loop(db_path, loop_id)
    assert row["state"] == "S3"
    assert row["decide_result"] == result
    return loop_id


def _seed_pivot_chain(
    db_path: Path,
    *,
    depth: int,
) -> list[str]:
    chain: list[str] = []
    parent_loop_id: str | None = None
    for index in range(depth):
        loop_id = _seed_running_loop(
            db_path,
            hypothesis=f"pivot-chain-{index}",
            acceptance=f"acceptance-{index}",
            parent_loop_id=parent_loop_id,
        )
        scrum_local.record_poc(loop_id, commit_sha=f"commit-{index:02d}")
        scrum_local.verify_loop(loop_id, observation=f"verified-{index}")
        scrum_local.decide_loop(loop_id, result="pivot", note=f"pivot-{index}")
        chain.append(loop_id)
        parent_loop_id = loop_id
    return chain


def test_s0_to_s1_state_transition_is_persisted(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-UPS-LIFE-001 / I-FK-001"""
    run_id = _seed_automation_run(fresh_db)
    slot_id = _seed_agent_slot(fresh_db, automation_run_id=run_id)
    loop_id = _seed_running_loop(fresh_db, forward_plan_id="PLAN-079", hypothesis="S0 to S1")

    scrum_local.record_poc(loop_id, commit_sha="commit-s0-s1", agent_slot_id=slot_id)

    loop_row = _fetch_scrum_loop(fresh_db, loop_id)
    slot_row = _fetch_agent_slot(fresh_db, slot_id)
    run_row = _fetch_automation_run(fresh_db, run_id)
    assert loop_row["state"] == "S1"
    assert loop_row["related_agent_slot_id"] == slot_id
    assert loop_row["forward_plan_id"] == "PLAN-079"
    assert slot_row["automation_run_id"] == run_id
    assert run_row["plan_id"] == "PLAN-079"
    assert run_row["trigger_actor"] == "system"
    assert run_row["status"] == "running"


def test_s1_to_s2_state_transition_is_persisted(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-UPS-LIFE-002"""
    loop_id = _seed_running_loop(fresh_db, hypothesis="S1 to S2")
    scrum_local.record_poc(loop_id, commit_sha="commit-s1")

    scrum_local.verify_loop(loop_id, observation="verify S1")

    loop_row = _fetch_scrum_loop(fresh_db, loop_id)
    assert loop_row["state"] == "S2"
    assert loop_row["decide_result"] is None
    assert loop_row["decided_at"] is None


def test_s2_to_s3_confirmed_transition_is_persisted(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-UPS-LIFE-003"""
    loop_id = _seed_verified_loop(fresh_db, result="confirmed")

    loop_row = _fetch_scrum_loop(fresh_db, loop_id)
    assert loop_row["state"] == "S3"
    assert loop_row["decide_result"] == "confirmed"
    assert loop_row["decided_at"] is not None
    assert loop_row["parent_loop_id"] is None


def test_s2_to_s3_rejected_transition_is_persisted(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-UPS-CLI-010"""
    loop_id = _seed_verified_loop(fresh_db, result="rejected")

    loop_row = _fetch_scrum_loop(fresh_db, loop_id)
    assert loop_row["state"] == "S3"
    assert loop_row["decide_result"] == "rejected"
    assert loop_row["decided_at"] is not None
    assert loop_row["parent_loop_id"] is None


def test_s2_to_s3_pivot_transition_sets_parent_loop_id(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-UPS-LIFE-005 / I-FK-003 / I-PIVOT-001"""
    parent_loop_id = _seed_verified_loop(fresh_db, result="pivot")
    child_loop_id = _seed_running_loop(
        fresh_db,
        hypothesis="pivot child",
        acceptance="child acceptance",
        parent_loop_id=parent_loop_id,
    )

    parent_row = _fetch_scrum_loop(fresh_db, parent_loop_id)
    child_row = _fetch_scrum_loop(fresh_db, child_loop_id)
    active_rows = scrum_local.list_active_loops("L4")

    assert parent_row["state"] == "S3"
    assert parent_row["decide_result"] == "pivot"
    assert child_row["state"] == "S0"
    assert child_row["parent_loop_id"] == parent_loop_id
    assert [row["loop_id"] for row in active_rows] == [child_loop_id]


def test_decided_loop_is_terminal_for_verify(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-UPS-LIFE-006"""
    loop_id = _seed_verified_loop(fresh_db, result="confirmed")

    with pytest.raises(ValueError, match="loop state must be S1"):
        scrum_local.verify_loop(loop_id, observation="double verify")

    loop_row = _fetch_scrum_loop(fresh_db, loop_id)
    assert loop_row["state"] == "S3"
    assert loop_row["decide_result"] == "confirmed"


def test_pivot_chain_creates_descendant_loop_with_new_root_state(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-PIVOT-001"""
    chain = _seed_pivot_chain(fresh_db, depth=1)
    parent_row = _fetch_scrum_loop(fresh_db, chain[0])
    child_loop_id = _seed_running_loop(
        fresh_db,
        hypothesis="descendant root",
        acceptance="descendant acceptance",
        parent_loop_id=chain[0],
    )
    child_row = _fetch_scrum_loop(fresh_db, child_loop_id)

    assert parent_row["state"] == "S3"
    assert parent_row["decide_result"] == "pivot"
    assert child_row["state"] == "S0"
    assert child_row["parent_loop_id"] == chain[0]


def test_pivot_chain_preserves_ancestor_trace_across_multiple_pivots(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-PIVOT-002"""
    root_loop_id = _seed_pivot_chain(fresh_db, depth=1)[0]
    child_loop_id = _seed_running_loop(
        fresh_db,
        hypothesis="second pivot child",
        acceptance="second pivot acceptance",
        parent_loop_id=root_loop_id,
    )
    scrum_local.record_poc(child_loop_id, commit_sha="commit-child")
    scrum_local.verify_loop(child_loop_id, observation="second pivot verify")
    scrum_local.decide_loop(child_loop_id, result="pivot", note="second pivot")
    grandchild_loop_id = _seed_running_loop(
        fresh_db,
        hypothesis="grandchild",
        acceptance="grandchild acceptance",
        parent_loop_id=child_loop_id,
    )

    root_row = _fetch_scrum_loop(fresh_db, root_loop_id)
    child_row = _fetch_scrum_loop(fresh_db, child_loop_id)
    grandchild_row = _fetch_scrum_loop(fresh_db, grandchild_loop_id)
    active_loop_ids = [row["loop_id"] for row in scrum_local.list_active_loops()]

    assert root_row["state"] == "S3"
    assert root_row["decide_result"] == "pivot"
    assert child_row["state"] == "S3"
    assert child_row["decide_result"] == "pivot"
    assert grandchild_row["state"] == "S0"
    assert grandchild_row["parent_loop_id"] == child_loop_id
    assert active_loop_ids == [grandchild_loop_id]
