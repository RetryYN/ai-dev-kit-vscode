import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _seed_design_review(
    db_path: Path,
    *,
    plan_id: str,
    layer: str,
    review_axis: str,
    verdict: str = "passed",
) -> None:
    conn = helix_db.get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO design_review (
                plan_id, layer, review_axis, source_layer, target_id, reviewed_at, reviewer, verdict, raw_findings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                layer,
                review_axis,
                "source-layer",
                1,
                "2026-05-13T00:00:00Z",
                "codex",
                verdict,
                "",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_query_design_review_pair_returns_true_for_both_axes(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))
    _seed_design_review(db_path, plan_id="PLAN-063", layer="architecture", review_axis="vertical")
    _seed_design_review(db_path, plan_id="PLAN-063", layer="architecture", review_axis="horizontal")

    result = helix_db.query_design_review_pair(db_path, plan_id="PLAN-063", layer="architecture")

    assert result == {"vertical_passed": True, "horizontal_passed": True}


def test_query_design_review_pair_returns_false_for_missing_horizontal(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))
    _seed_design_review(db_path, plan_id="PLAN-063", layer="architecture", review_axis="vertical")

    result = helix_db.query_design_review_pair(db_path, plan_id="PLAN-063", layer="architecture")

    assert result == {"vertical_passed": True, "horizontal_passed": False}


def test_query_design_review_pair_returns_false_for_missing_pair(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))

    result = helix_db.query_design_review_pair(db_path, plan_id="PLAN-063", layer="architecture")

    assert result == {"vertical_passed": False, "horizontal_passed": False}
