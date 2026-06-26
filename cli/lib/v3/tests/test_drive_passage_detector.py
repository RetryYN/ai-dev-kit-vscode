from __future__ import annotations

import sqlite3

from cli.lib.v3.detectors.core import (
    DrivePassageInput,
    analyze_drive_passage,
    drive_passage_messages,
)
from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate


def test_driving_plan_without_forward_return_flagged():
    inp = DrivePassageInput(drive_plan_ids=("P-1", "P-2"), forward_return_plan_ids=frozenset({"P-1"}))
    res = analyze_drive_passage(inp)
    assert res.ok is False
    assert res.missing_forward_return == ("P-2",)
    assert drive_passage_messages(res)[0].subject == "P-2"


def test_all_driving_plans_with_forward_return_ok():
    inp = DrivePassageInput(drive_plan_ids=("P-1",), forward_return_plan_ids=frozenset({"P-1"}))
    assert analyze_drive_passage(inp).ok is True


def test_no_driving_plans_is_ok_not_absence_blind():
    # 駆動 PLAN 0 件 = 検査対象なし = ok(should-be 集合を正しく空と判定)
    assert analyze_drive_passage(DrivePassageInput(drive_plan_ids=(), forward_return_plan_ids=frozenset())).ok is True


def test_forward_return_edge_projected_for_driving_plan(tmp_path):
    (tmp_path / "r.md").write_text(
        '---\nplan_id: PLAN-R-1\nkind: refactor\nlayer: L7\ndrive: be\nstatus: draft\n'
        'forward_return: "L7 へ戻す"\n---\nbody\n',
        encoding="utf-8",
    )
    db = sqlite3.connect(":memory:"); migrate(db)
    rebuild_projection(db, str(tmp_path))
    edges = db.execute(
        "select from_artifact from trace_edges where edge_kind='forward_return'"
    ).fetchall()
    assert ("PLAN-R-1",) in edges
