"""DoD 検証: PLAN-079-integration-test-design.md
対象実装: cli/lib/reverse_local.py
結合テスト範囲:
  - I-SRF-LIFE-001 / I-SRF-LIFE-002 / I-SRF-LIFE-004 / I-SRF-LIFE-005 / I-SRF-LIFE-006
  - I-FK-002 / I-ROUTE-001 / I-ROUTE-002 / I-ROUTE-003
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
import reverse_local
import scrum_local


def _fetch_scrum_loop(db_path: Path, loop_id: str) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM scrum_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _fetch_reverse_loop(db_path: Path, loop_id: str) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM reverse_local_loops WHERE loop_id = ?", (loop_id,)).fetchone()
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


def _seed_confirmed_scrum_loop(db_path: Path, *, result: str = "confirmed") -> str:
    loop_id = scrum_local.init_local_loop(
        forward_layer="L4",
        forward_plan_id="PLAN-079",
        hypothesis="reverse seed",
        acceptance="reverse acceptance",
    )
    scrum_local.record_poc(loop_id, commit_sha="seed-commit")
    scrum_local.verify_loop(loop_id, observation="seed verify")
    scrum_local.decide_loop(loop_id, result=result, note=f"seed result={result}")
    row = _fetch_scrum_loop(db_path, loop_id)
    assert row["state"] == "S3"
    assert row["decide_result"] == result
    return loop_id


def _seed_reverse_loop_at_r3(db_path: Path, scrum_loop_id: str) -> str:
    loop_id = reverse_local.init_from_scrum(scrum_loop_id)
    reverse_local.transition_state(loop_id, "R1")
    reverse_local.transition_state(loop_id, "R2")
    reverse_local.transition_state(loop_id, "R3")
    row = _fetch_reverse_loop(db_path, loop_id)
    assert row["state"] == "R3"
    return loop_id


def _advance_reverse_loop_to_r4(db_path: Path, scrum_loop_id: str) -> str:
    loop_id = _seed_reverse_loop_at_r3(db_path, scrum_loop_id)
    reverse_local.transition_state(loop_id, "R4")
    row = _fetch_reverse_loop(db_path, loop_id)
    assert row["state"] == "R4"
    return loop_id


def test_confirmed_scrum_loop_can_spawn_reverse_loop(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-SRF-LIFE-001 / I-FK-002"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)

    reverse_loop_id = reverse_local.init_from_scrum(scrum_loop_id)

    scrum_row = _fetch_scrum_loop(fresh_db, scrum_loop_id)
    reverse_row = _fetch_reverse_loop(fresh_db, reverse_loop_id)
    assert scrum_row["state"] == "S3"
    assert scrum_row["decide_result"] == "confirmed"
    assert reverse_row["state"] == "R0"
    assert reverse_row["parent_scrum_loop_id"] == scrum_loop_id
    assert reverse_row["reverse_type"] == "scrum-to-forward"


def test_reverse_from_scrum_requires_confirmed_scrum_loop(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-SRF-CLI-002"""
    running_loop_id = scrum_local.init_local_loop(
        forward_layer="L4",
        forward_plan_id="PLAN-079",
        hypothesis="running seed",
        acceptance="running acceptance",
    )
    rejected_loop_id = _seed_confirmed_scrum_loop(fresh_db, result="rejected")

    with pytest.raises(ValueError, match="confirmed scrum loop does not exist"):
        reverse_local.init_from_scrum(running_loop_id)
    with pytest.raises(ValueError, match="confirmed scrum loop does not exist"):
        reverse_local.init_from_scrum(rejected_loop_id)

    conn = helix_db.get_connection(fresh_db)
    try:
        rows = conn.execute("SELECT loop_id, parent_scrum_loop_id FROM reverse_local_loops").fetchall()
    finally:
        conn.close()
    assert rows == []


def test_reverse_local_stage_advances_to_r1(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-SRF-CLI-003"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)
    reverse_loop_id = reverse_local.init_from_scrum(scrum_loop_id)

    reverse_local.transition_state(reverse_loop_id, "R1")

    row = _fetch_reverse_loop(fresh_db, reverse_loop_id)
    assert row["state"] == "R1"


def test_reverse_local_stage_advances_to_r2_and_r3(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-SRF-CLI-004 / I-SRF-LIFE-004 / I-SRF-LIFE-005"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)
    reverse_loop_id = reverse_local.init_from_scrum(scrum_loop_id)

    reverse_local.transition_state(reverse_loop_id, "R1")
    reverse_local.transition_state(reverse_loop_id, "R2")
    row_r2 = _fetch_reverse_loop(fresh_db, reverse_loop_id)
    assert row_r2["state"] == "R2"

    reverse_local.transition_state(reverse_loop_id, "R3")
    row_r3 = _fetch_reverse_loop(fresh_db, reverse_loop_id)
    assert row_r3["state"] == "R3"


def test_reverse_r0_evidence_acquisition_persists_artifact_links(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-SRF-LIFE-002"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)
    reverse_loop_id = _advance_reverse_loop_to_r4(fresh_db, scrum_loop_id)
    artifact_links = [
        {"kind": "commit", "ref": "abc1234"},
        {"kind": "audit", "ref": "audit-001"},
    ]

    reverse_local.route_to_forward(
        reverse_loop_id,
        target_plan="PLAN-079",
        target_layer="L4",
        artifact_links=artifact_links,
    )

    row = _fetch_reverse_loop(fresh_db, reverse_loop_id)
    assert row["state"] == "R4"
    assert row["target_forward_plan"] == "PLAN-079"
    assert row["target_forward_layer"] == "L4"
    assert row["routed_at"] is not None
    assert json.loads(row["artifact_links"]) == artifact_links


def test_reverse_r4_routing_marks_completed_and_closed(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-SRF-LIFE-006 / I-ROUTE-001"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)
    reverse_loop_id = _advance_reverse_loop_to_r4(fresh_db, scrum_loop_id)

    reverse_local.route_to_forward(
        reverse_loop_id,
        target_plan="PLAN-079",
        target_layer="L4",
    )

    row = _fetch_reverse_loop(fresh_db, reverse_loop_id)
    assert row["state"] == "R4"
    assert row["target_forward_plan"] == "PLAN-079"
    assert row["target_forward_layer"] == "L4"
    assert row["routed_at"] is not None
    assert row["artifact_links"] is None


def test_r4_route_rejects_missing_forward_plan(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-ROUTE-002"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)
    reverse_loop_id = _advance_reverse_loop_to_r4(fresh_db, scrum_loop_id)

    with pytest.raises(ValueError, match="must be non-empty"):
        reverse_local.route_to_forward(reverse_loop_id, target_plan=" ", target_layer="L4")


def test_r4_route_rejects_invalid_forward_layer(fresh_db: Path) -> None:
    """DoD 検証: PLAN-079-integration-test-design.md I-ROUTE-003"""
    scrum_loop_id = _seed_confirmed_scrum_loop(fresh_db)
    reverse_loop_id = _advance_reverse_loop_to_r4(fresh_db, scrum_loop_id)

    with pytest.raises(ValueError, match="invalid target_layer"):
        reverse_local.route_to_forward(reverse_loop_id, target_plan="PLAN-079", target_layer="L9")

