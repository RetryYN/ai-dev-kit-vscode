from __future__ import annotations

import sqlite3

from cli.lib.v3.detectors.core import FnUtPairInput, analyze_fn_ut_pair, fn_ut_pair_messages
from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate


def test_l6_required_without_covering_ut_flagged():
    res = analyze_fn_ut_pair(FnUtPairInput(l6_required_fns=("FR-A-1", "FR-B-2"), covered_fns=frozenset({"FR-A-1"})))
    assert res.ok is False
    assert res.unpaired_fns == ("FR-B-2",)
    assert fn_ut_pair_messages(res)[0].subject == "FR-B-2"


def test_all_l6_required_covered_ok():
    assert analyze_fn_ut_pair(FnUtPairInput(l6_required_fns=("FR-A-1",), covered_fns=frozenset({"FR-A-1"}))).ok is True


def test_no_l6_required_is_ok():
    assert analyze_fn_ut_pair(FnUtPairInput(l6_required_fns=(), covered_fns=frozenset())).ok is True


def test_covers_anchor_projects_fr_id(tmp_path):
    (tmp_path / "test_x.py").write_text("# @covers FR-X-001\ndef test_a():\n    pass\n", encoding="utf-8")
    db = sqlite3.connect(":memory:"); migrate(db)
    rebuild_projection(db, str(tmp_path))
    assert db.execute("select fr_id from test_cases").fetchone() == ("FR-X-001",)
