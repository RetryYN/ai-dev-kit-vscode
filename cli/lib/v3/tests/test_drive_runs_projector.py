from __future__ import annotations

import sqlite3

from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate


def _fresh_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    migrate(db)
    return db


def test_driving_kind_plan_becomes_drive_run(tmp_path):
    (tmp_path / "refactor-plan.md").write_text(
        "---\nplan_id: PLAN-R-1\nkind: refactor\nlayer: L7\ndrive: be\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    rows = db.execute("select plan_id, kind, mode, drive from drive_runs").fetchall()
    assert rows == [("PLAN-R-1", "refactor", "refactor", "be")]


def test_non_driving_kind_not_in_drive_runs(tmp_path):
    (tmp_path / "impl-plan.md").write_text(
        "---\nplan_id: PLAN-I-1\nkind: impl\nlayer: L7\ndrive: be\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    assert db.execute("select count(*) from drive_runs").fetchone()[0] == 0


def test_drive_runs_idempotent(tmp_path):
    (tmp_path / "rev.md").write_text(
        "---\nplan_id: PLAN-V-1\nkind: reverse\nlayer: L3\ndrive: reverse\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    n1 = db.execute("select count(*) from drive_runs").fetchone()[0]
    rebuild_projection(db, str(tmp_path))
    n2 = db.execute("select count(*) from drive_runs").fetchone()[0]
    assert n1 == n2 == 1
