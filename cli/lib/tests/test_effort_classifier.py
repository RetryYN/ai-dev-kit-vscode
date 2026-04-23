import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import effort_classifier


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
        effort_classifier,
        "call_classifier",
        lambda *args, **kwargs: {"effort": "xhigh", "score": 13},
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
