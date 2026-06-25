from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cli.lib.v3.projection.sources import load_sources
from cli.lib.v3.projection.writer import rebuild_projection
from cli.lib.v3.schema.ddl import migrate
from cli.lib.v3.schema.registry import TABLES

REPO_ROOT = Path(__file__).resolve().parents[4]


def _snapshot_db(conn: sqlite3.Connection) -> dict[str, list[tuple[object, ...]]]:
    snapshot: dict[str, list[tuple[object, ...]]] = {}
    for table in sorted(table.name for table in TABLES):
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        order_by = ", ".join(str(index) for index in range(1, len(columns) + 1))
        snapshot[table] = conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()
    return snapshot


@pytest.fixture()
def migrated_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    try:
        yield conn
    finally:
        conn.close()


def test_ut_p7_01_load_sources_parses_nested_frontmatter_lists(tmp_path: Path) -> None:
    """DoD 検証: L7-v3-engine-phase7-core-projectorsplan UT-P7-01"""
    plan_path = tmp_path / "docs/plans/L7/sample-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "---\r\n"
        "plan_id: PLAN-NESTED\r\n"
        "kind: impl\r\n"
        "layer: L7\r\n"
        "drive: be\r\n"
        "status: draft\r\n"
        "dependencies:\r\n"
        "  requires:\r\n"
        "    - PLAN-BASE\r\n"
        "  blocks: []\r\n"
        "generates:\r\n"
        "  - artifact_path: cli/lib/v3/projection/sources.py\r\n"
        "    artifact_type: python_module\r\n"
        "pairs_test_design:\r\n"
        "  - cli/lib/v3/tests/test_core_projectors.py\r\n"
        "---\r\n"
        "\r\n"
        "body\r\n",
        encoding="utf-8",
    )

    [record] = load_sources(tmp_path)

    assert record.parse_error is None
    assert record.frontmatter["dependencies"] == {"requires": ["PLAN-BASE"], "blocks": []}
    assert record.frontmatter["generates"] == [
        {
            "artifact_path": "cli/lib/v3/projection/sources.py",
            "artifact_type": "python_module",
        }
    ]
    assert record.frontmatter["pairs_test_design"] == ["cli/lib/v3/tests/test_core_projectors.py"]


def test_ut_p7_02_real_l7_plans_populate_plan_registry_without_parse_failures(
    migrated_db: sqlite3.Connection,
) -> None:
    """DoD 検証: L7-v3-engine-phase7-core-projectorsplan UT-P7-02"""
    sources = load_sources(REPO_ROOT / "docs/plans")

    result = rebuild_projection(migrated_db, sources)

    assert result.fails == ()
    assert all(source.parse_error is None for source in sources)
    assert migrated_db.execute("SELECT count(*) FROM plan_registry").fetchone()[0] > 0
    assert migrated_db.execute("SELECT count(*) FROM findings WHERE kind='invalid-frontmatter'").fetchone()[0] == 0


def test_ut_p7_03_real_l7_projection_is_bit_identical_and_emits_bidirectional_trace_edges(
    migrated_db: sqlite3.Connection,
) -> None:
    """DoD 検証: L7-v3-engine-phase7-core-projectorsplan UT-P7-03"""
    sources = load_sources(REPO_ROOT / "docs/plans")

    rebuild_projection(migrated_db, sources)
    first = _snapshot_db(migrated_db)

    rebuild_projection(migrated_db, load_sources(REPO_ROOT / "docs/plans"))
    second = _snapshot_db(migrated_db)

    trace_edges = {
        (from_artifact, to_artifact, edge_kind)
        for from_artifact, to_artifact, edge_kind in migrated_db.execute(
            "SELECT from_artifact, to_artifact, edge_kind FROM trace_edges"
        ).fetchall()
    }
    plan_path = "L7/L7-v3-engine-phase7-core-projectorsplan.md"
    generated_path = "cli/lib/v3/projection/sources.py"

    assert first == second
    assert (plan_path, generated_path, "generates") in trace_edges
    assert (generated_path, plan_path, "generated_by") in trace_edges
