import json
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import effort_classifier
import helix_db
from llm_classifier_base import LLMClassifierBase


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    return db_path


def test_files_score_boundary_values() -> None:
    assert effort_classifier._files_score(2) == 1
    assert effort_classifier._files_score(3) == 2
    assert effort_classifier._files_score(5) == 2
    assert effort_classifier._files_score(6) == 3


def test_score_task_adds_line_penalty_only_over_500() -> None:
    base = effort_classifier.score_task("refactor API migration test", files=3, lines=500)
    over = effort_classifier.score_task("refactor API migration test", files=3, lines=501)

    assert base["score"] == 12
    assert over["score"] == 14


def test_map_to_effort_boundaries() -> None:
    assert effort_classifier.map_to_effort(3) == "low"
    assert effort_classifier.map_to_effort(4) == "medium"
    assert effort_classifier.map_to_effort(7) == "medium"
    assert effort_classifier.map_to_effort(8) == "high"
    assert effort_classifier.map_to_effort(12) == "high"
    assert effort_classifier.map_to_effort(13) == "xhigh"


def test_classify_uses_llm_result_on_boundary_score(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(effort_classifier, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(
        effort_classifier,
        "score_task",
        lambda *args, **kwargs: {
            "score": 12,
            "breakdown": {
                "files": 3,
                "cross_module": 2,
                "spec_understanding": 2,
                "side_effect": 4,
                "test_complexity": 1,
            },
        },
    )
    monkeypatch.setattr(
        effort_classifier.EffortClassifier,
        "_invoke_codex",
        lambda self, query, context: '{"effort": "xhigh", "score": 13}',
    )

    result = effort_classifier.classify(
        "API migration test",
        role="qa",
        size="S",
        files=1,
        lines=10,
        use_llm=True,
    )

    assert result["score"] == 12
    assert result["effort"] == "xhigh"
    assert result["split_recommended"] is True
    assert result["llm_used"] is True
    assert result["recommended_thinking"] == "xhigh"


def test_classify_skips_llm_for_non_boundary_score(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(effort_classifier, "CACHE_DIR", tmp_path)

    def _fail_invoke(self, query, context):
        raise AssertionError("LLM should not be called for non-boundary scores")

    monkeypatch.setattr(effort_classifier.EffortClassifier, "_invoke_codex", _fail_invoke)

    result = effort_classifier.classify(
        "small maintenance",
        role="qa",
        size="M",
        files=1,
        lines=10,
        use_llm=True,
    )

    assert result["score"] == 5
    assert result["effort"] == "medium"
    assert result["llm_used"] is False
    assert result["cached"] is False


def test_classify_calls_llm_for_boundary_score(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(effort_classifier, "CACHE_DIR", tmp_path)
    calls = {"invoke": 0}

    monkeypatch.setattr(
        effort_classifier,
        "score_task",
        lambda *args, **kwargs: {
            "score": 12,
            "breakdown": {
                "files": 3,
                "cross_module": 2,
                "spec_understanding": 2,
                "side_effect": 4,
                "test_complexity": 1,
            },
        },
    )

    def _fake_invoke(self, query, context):
        calls["invoke"] += 1
        return '{"effort": "xhigh", "score": 13}'

    monkeypatch.setattr(effort_classifier.EffortClassifier, "_invoke_codex", _fake_invoke)

    result = effort_classifier.classify(
        "API migration test",
        role="qa",
        size="S",
        files=1,
        lines=10,
        use_llm=True,
    )

    assert calls["invoke"] == 1
    assert result["score"] == 12
    assert result["effort"] == "xhigh"
    assert result["llm_used"] is True


def test_classify_returns_cached_result_on_second_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(effort_classifier, "CACHE_DIR", tmp_path)

    first = effort_classifier.classify("bug fix", role="qa", size="M", files=1, lines=10, use_llm=False)
    second = effort_classifier.classify("bug fix", role="qa", size="M", files=1, lines=10, use_llm=False)

    assert first["cached"] is False
    assert second["cached"] is True
    assert second["effort"] == first["effort"]


def test_effort_classifier_uses_base_class() -> None:
    assert isinstance(effort_classifier.EffortClassifier(), LLMClassifierBase)


def test_effort_classifier_records_to_entries(tmp_path: Path) -> None:
    classifier = effort_classifier.EffortClassifier(db_path=_init_db(tmp_path))
    classifier.cache_dir = tmp_path / "effort-cache"

    result = classifier.classify("small bug fix", role="qa", size="S", files=1, lines=8, use_llm=False)

    conn = helix_db.get_connection(classifier.db_path)
    try:
        row = conn.execute(
            "SELECT * FROM entries WHERE id LIKE 'effort_classifier.%'",
        ).fetchone()
    finally:
        conn.close()

    assert result["effort"] == "medium"
    assert row is not None
    assert row["axis"] == "evidence"
    metadata = json.loads(row["metadata"])
    assert metadata["query"] == "small bug fix"
    assert metadata["source"] == "rule"
    assert metadata["result"]["effort"] == "medium"


def test_effort_classify_returns_dict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _init_db(tmp_path)
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    monkeypatch.setattr(effort_classifier, "CACHE_DIR", tmp_path / "effort-cache")

    result = effort_classifier.effort_classify(
        "API migration refactor test",
        role="qa",
        size="M",
        files=4,
        lines=100,
        use_llm=False,
    )

    assert isinstance(result, dict)
    assert {"effort", "score", "recommended_thinking", "cached"} <= set(result)
