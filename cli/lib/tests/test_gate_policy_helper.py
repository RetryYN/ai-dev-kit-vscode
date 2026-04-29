import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from gate_policy_helper import compute_weighted_score, load_accuracy_weights


POLICY_PATH = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "tools"
    / "ai-coding"
    / "references"
    / "gate-policy.md"
)


def test_load_accuracy_weights_parses_all_gates() -> None:
    weights = load_accuracy_weights(POLICY_PATH)

    assert set(weights) == {
        "G0.5",
        "G1",
        "G1.5",
        "G1R",
        "G2",
        "G3",
        "G4",
        "G5",
        "G6",
        "G7",
    }


def test_load_accuracy_weights_returns_correct_g3_weight() -> None:
    weights = load_accuracy_weights(POLICY_PATH)

    assert weights["G3"] == 0.9


def test_load_accuracy_weights_returns_correct_g4_weight() -> None:
    weights = load_accuracy_weights(POLICY_PATH)

    assert weights["G4"] == 0.95


def test_load_accuracy_weights_handles_missing_file(tmp_path: Path) -> None:
    assert load_accuracy_weights(tmp_path / "missing-gate-policy.md") == {}


def test_compute_weighted_score_with_5_lv3() -> None:
    scores = [
        {"dimension": "density", "level": 3, "comment": ""},
        {"dimension": "depth", "level": 3, "comment": ""},
        {"dimension": "breadth", "level": 3, "comment": ""},
        {"dimension": "accuracy", "level": 3, "comment": ""},
        {"dimension": "maintainability", "level": 3, "comment": ""},
    ]

    assert compute_weighted_score(scores, 0.9) == 2.7


def test_compute_weighted_score_empty_scores() -> None:
    assert compute_weighted_score([], 0.9) == 0.0


def test_compute_weighted_score_invalid_levels() -> None:
    scores = [
        {"dimension": "density", "level": "3", "comment": ""},
        {"dimension": "depth", "level": 2, "comment": ""},
        {"dimension": "breadth", "level": None, "comment": ""},
        {"dimension": "accuracy", "level": 4, "comment": ""},
    ]

    assert compute_weighted_score(scores, 0.5) == 1.5
