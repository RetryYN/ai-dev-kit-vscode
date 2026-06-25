from __future__ import annotations

import sqlite3

from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate


def _fresh_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    migrate(db)
    return db


def test_project_code_registers_py_and_bats(tmp_path):
    (tmp_path / "foo.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "bar.bats").write_text("@test 'x' { true; }\n", encoding="utf-8")
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    rows = dict(
        db.execute(
            "select path, artifact_type from artifact_registry "
            "where artifact_type in ('python_module','script')"
        ).fetchall()
    )
    assert rows.get("foo.py") == "python_module"
    assert rows.get("bar.bats") == "script"


def test_project_code_no_body_stored(tmp_path):
    # C-5: code 本文を DB に保存しない（path/type のみ、本文は artifact_registry に入れない）
    marker = "DISTINCTIVE_BODY_MARKER_ZZ9_DO_NOT_STORE"
    (tmp_path / "leak.py").write_text(f"x = {marker!r}\n", encoding="utf-8")
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    dump = "".join(
        str(r) for r in db.execute("select * from artifact_registry").fetchall()
    )
    assert marker not in dump


def test_project_code_idempotent(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.bats").write_text("@test 'y' { true; }\n", encoding="utf-8")
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    n1 = db.execute("select count(*) from artifact_registry").fetchone()[0]
    rebuild_projection(db, str(tmp_path))
    n2 = db.execute("select count(*) from artifact_registry").fetchone()[0]
    assert n1 == n2 and n1 >= 2
