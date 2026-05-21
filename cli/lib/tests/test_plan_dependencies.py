from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_dependencies


def _prepare_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "docs" / "plans").mkdir(parents=True)
    return project


def _write_plan(project: Path, plan_id: str, dependencies: str) -> None:
    plan_path = project / "docs" / "plans" / f"{plan_id}-sample.md"
    plan_path.write_text(
        "\n".join(
            [
                "---",
                f"plan_id: {plan_id}",
                "title: Sample Plan",
                "kind: impl",
                "layer: L4",
                "drive: be",
                "status: draft",
                dependencies.strip("\n"),
                "---",
                "",
                "# Body",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_load_dependencies_returns_dict(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    _write_plan(
        project,
        "PLAN-101",
        """
dependencies:
  parent: PLAN-100
  requires:
    - PLAN-099
  blocks:
    - PLAN-102
""",
    )

    result = plan_dependencies.load_dependencies("PLAN-101", project)

    assert result == {
        "parent": "PLAN-100",
        "requires": ["PLAN-099"],
        "blocks": ["PLAN-102"],
    }


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"

    plan_dependencies.save_dependencies(
        "PLAN-200",
        {"parent": "PLAN-100", "requires": ["PLAN-150"], "blocks": ["PLAN-250"]},
        db_path.as_posix(),
    )

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT dep_type, dep_plan_id
            FROM plan_dependencies
            WHERE plan_id = ?
            ORDER BY dep_type, dep_plan_id
            """,
            ("PLAN-200",),
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("blocks", "PLAN-250"),
        ("parent", "PLAN-100"),
        ("requires", "PLAN-150"),
    ]


def test_check_reciprocal_detects_missing_blocks(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    _write_plan(
        project,
        "PLAN-300",
        """
dependencies:
  parent: null
  requires:
    - PLAN-301
  blocks: []
""",
    )
    _write_plan(
        project,
        "PLAN-301",
        """
dependencies:
  parent: null
  requires: []
  blocks: []
""",
    )

    warnings = plan_dependencies.check_reciprocal("PLAN-300", project)

    assert warnings == ["WARN: PLAN-300 requires PLAN-301 but PLAN-301 does not block PLAN-300"]


def test_build_graph_returns_dict(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    _write_plan(
        project,
        "PLAN-400",
        """
dependencies:
  parent: null
  requires:
    - PLAN-401
  blocks: []
""",
    )
    _write_plan(
        project,
        "PLAN-401",
        """
dependencies:
  parent: null
  requires: []
  blocks:
    - PLAN-400
""",
    )

    graph = plan_dependencies.build_graph(project)

    assert isinstance(graph, dict)
    assert graph["PLAN-400"]["requires"] == ["PLAN-401"]
    assert graph["PLAN-401"]["blocks"] == ["PLAN-400"]
