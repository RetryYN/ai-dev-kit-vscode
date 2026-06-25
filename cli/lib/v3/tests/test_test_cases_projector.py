from __future__ import annotations

import sqlite3

from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate


def _fresh_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    migrate(db)
    return db


def test_py_test_functions_become_test_cases(tmp_path):
    (tmp_path / "test_sample.py").write_text(
        "def test_alpha():\n    pass\n\n"
        "def test_beta():\n    pass\n\n"
        "def helper():\n    pass\n",
        encoding="utf-8",
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    names = {r[0] for r in db.execute("select test_name from test_cases").fetchall()}
    assert names == {"test_alpha", "test_beta"}  # helper() excluded
    kinds = {r[0] for r in db.execute("select kind from test_cases").fetchall()}
    assert kinds == {"unit"}


def test_bats_tests_become_test_cases(tmp_path):
    (tmp_path / "sample.bats").write_text(
        "@test 'does a thing' { true; }\n@test \"does another\" { true; }\n",
        encoding="utf-8",
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    rows = {(r[0], r[1]) for r in db.execute("select test_name, kind from test_cases").fetchall()}
    assert rows == {("does a thing", "bats"), ("does another", "bats")}


def test_test_cases_idempotent(tmp_path):
    (tmp_path / "test_x.py").write_text("def test_one():\n    pass\n", encoding="utf-8")
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    n1 = db.execute("select count(*) from test_cases").fetchone()[0]
    rebuild_projection(db, str(tmp_path))
    n2 = db.execute("select count(*) from test_cases").fetchone()[0]
    assert n1 == n2 == 1
