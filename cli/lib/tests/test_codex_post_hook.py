import io
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import codex_post_hook
import helix_db


SAMPLE_REVIEW_OUTPUT = """{
  "verdict": "approve",
  "summary": "ok",
  "overall_scores": [
    {"dimension": "density", "level": 4, "comment": "dense"},
    {"dimension": "depth", "level": 3, "comment": "deep enough"},
    {"dimension": "breadth", "level": 4, "comment": "broad"},
    {"dimension": "accuracy", "level": 5, "comment": "accurate"},
    {"dimension": "maintainability", "level": 4, "comment": "maintainable"}
  ],
  "findings": [],
  "next_steps": []
}
"""


def _rows(db_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM accuracy_score ORDER BY dimension").fetchall()
    finally:
        conn.close()


def test_extract_overall_scores_from_log() -> None:
    log_text = f"header\n{SAMPLE_REVIEW_OUTPUT}\nfooter\n"
    scores = codex_post_hook.extract_overall_scores_from_text(log_text)

    assert scores is not None
    assert [score["dimension"] for score in scores] == list(codex_post_hook.DIMENSIONS)
    assert scores[3]["level"] == 5


def test_insert_accuracy_score(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))
    scores = codex_post_hook.extract_overall_scores_from_text(SAMPLE_REVIEW_OUTPUT)
    assert scores is not None

    inserted = codex_post_hook.insert_accuracy_scores(
        str(db_path),
        plan_id="PLAN-043",
        run_id="20260510-120000-tl-PLAN-043-W-4",
        scores=scores,
    )

    rows = _rows(db_path)
    assert inserted == 5
    assert len(rows) == 5
    assert {row["gate"] for row in rows} == {"PLAN_REVIEW"}
    assert {row["reviewer"] for row in rows} == {"codex-tl"}
    assert rows[0]["evidence"].startswith("source=helix-codex-post-hook\nrun_id=20260510-120000")


def test_skip_duplicate_insert(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))
    scores = codex_post_hook.extract_overall_scores_from_text(SAMPLE_REVIEW_OUTPUT)
    assert scores is not None

    first = codex_post_hook.insert_accuracy_scores(
        str(db_path),
        plan_id="PLAN-043",
        run_id="same-run",
        scores=scores,
    )
    second = codex_post_hook.insert_accuracy_scores(
        str(db_path),
        plan_id="PLAN-043",
        run_id="same-run",
        scores=scores,
    )

    assert first == 5
    assert second == 0
    assert len(_rows(db_path)) == 5


def test_fail_open_on_extraction_failure(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(str(db_path))
    stderr = io.StringIO()

    inserted = codex_post_hook.record_post_review_scores(
        str(db_path),
        plan_id="PLAN-043",
        run_id="missing-scores",
        stdout_text="not a review payload",
        stderr=stderr,
    )

    assert inserted == 0
    assert _rows(db_path) == []
    assert "WARN: codex post-hook skipped" in stderr.getvalue()
