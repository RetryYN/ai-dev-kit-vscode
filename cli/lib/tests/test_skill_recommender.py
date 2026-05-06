import json
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import skill_recommender
from llm_classifier_base import LLMClassifierBase
from skill_recommender import SkillRecommender


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    return db_path


def _fetch_entry(db_path: Path, prefix: str) -> sqlite3.Row:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM entries WHERE id LIKE ?",
            (f"{prefix}.%",),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def _recommender(tmp_path: Path) -> SkillRecommender:
    classifier = SkillRecommender(db_path=_init_db(tmp_path))
    classifier.cache_dir = tmp_path / "cache" / classifier.classifier_name
    classifier._top_n = 1
    classifier._task_text = "testing task"
    return classifier


def test_skill_recommender_uses_base_class() -> None:
    assert isinstance(SkillRecommender(), LLMClassifierBase)


def test_skill_recommender_records_to_entries(tmp_path: Path, monkeypatch) -> None:
    classifier = _recommender(tmp_path)

    monkeypatch.setattr(
        classifier,
        "_invoke_codex",
        lambda query, context: json.dumps(
            {
                "recommendations": [
                    {
                        "skill_id": "common/testing",
                        "score": 0.97,
                        "reason": "matches test work",
                        "recommended_agent": "qa",
                    }
                ]
            }
        ),
    )

    result = classifier.classify("testing task", {"prompt": "recommend testing", "top_n": 1})

    assert result["candidates"][0]["skill_id"] == "common/testing"
    row = _fetch_entry(classifier.db_path, classifier.classifier_name)
    assert row["axis"] == "evidence"
    assert row["agent_actor"].startswith("codex-")
    metadata = json.loads(row["metadata"])
    assert metadata["query"] == "testing task"
    assert metadata["source"] == "codex"
    assert metadata["result"]["candidates"][0]["skill_id"] == "common/testing"


def test_skill_search_returns_list_of_skills(monkeypatch) -> None:
    monkeypatch.setattr(
        skill_recommender,
        "recommend",
        lambda query, top_n: {
            "candidates": [
                {"skill_id": "common/testing", "score": 0.9, "recommended_agent": "qa"},
                {"skill_id": "workflow/verification", "score": 0.8, "recommended_agent": "tl"},
            ]
        },
    )

    result = skill_recommender.skill_search("write tests", n=2)

    assert result == [
        {"id": "common/testing", "score": 0.9, "agent": "qa"},
        {"id": "workflow/verification", "score": 0.8, "agent": "tl"},
    ]
