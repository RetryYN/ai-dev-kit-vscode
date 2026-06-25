from __future__ import annotations

import sqlite3

from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate


def _fresh_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    migrate(db)
    return db


def test_functional_registry_from_yaml(tmp_path):
    (tmp_path / "functional-registry.yaml").write_text(
        "entries:\n"
        "  - id: FR-X-001\n"
        "    l1_fr: FR-L1-1\n"
        "    l3_fr: FR-L3-1\n"
        "    coverage_layer: L4\n"
        "  - id: FR-X-002\n"
        "    coverage_layer: L6\n",
        encoding="utf-8",
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    rows = {r[0]: r[1] for r in db.execute("select fn_id, layer from functional_registry").fetchall()}
    assert rows == {"FR-X-001": "L4", "FR-X-002": "L6"}


def test_functional_registry_idempotent(tmp_path):
    (tmp_path / "functional-registry.yaml").write_text(
        "entries:\n  - id: FR-Y-001\n    coverage_layer: L4\n", encoding="utf-8"
    )
    db = _fresh_db()
    rebuild_projection(db, str(tmp_path))
    n1 = db.execute("select count(*) from functional_registry").fetchone()[0]
    rebuild_projection(db, str(tmp_path))
    n2 = db.execute("select count(*) from functional_registry").fetchone()[0]
    assert n1 == n2 == 1
