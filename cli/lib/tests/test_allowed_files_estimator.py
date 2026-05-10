import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import allowed_files_estimator


MODULE_PATH = LIB_DIR / "allowed_files_estimator.py"


def write_file(path: Path, content: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_repo_fixture(tmp_path: Path) -> Path:
    write_file(tmp_path / "cli/helix-codex")
    write_file(tmp_path / "cli/lib/allowed_files_estimator.py")
    write_file(tmp_path / "cli/lib/tests/test_allowed_files_estimator.py")
    write_file(tmp_path / "cli/lib/codex_post_validation.py")
    write_file(tmp_path / "docs/allowed_files_notes.md")
    return tmp_path


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_extract_keywords() -> None:
    keywords = allowed_files_estimator.extract_keywords(
        "Implement cli/helix-codex and cli/lib/allowed_files_estimator.py for auto-allowed-files"
    )

    assert "cli/helix-codex" in keywords
    assert "cli/lib/allowed_files_estimator.py" in keywords
    assert "allowed_files_estimator" in keywords
    assert "helix-codex" in keywords


def test_find_matching_files(tmp_path: Path) -> None:
    repo_root = create_repo_fixture(tmp_path)

    matches = allowed_files_estimator.find_matching_files(
        ["cli/lib/allowed_files_estimator.py", "allowed_files_estimator"],
        repo_root,
    )

    assert matches == [Path("cli/lib/allowed_files_estimator.py")]


def test_high_confidence(tmp_path: Path) -> None:
    repo_root = create_repo_fixture(tmp_path)
    task = (
        "Implement cli/helix-codex, cli/lib/allowed_files_estimator.py, "
        "and cli/lib/tests/test_allowed_files_estimator.py"
    )

    candidates, confidence, low_confidence = allowed_files_estimator.estimate_allowed_files(
        task,
        repo_root,
    )

    assert set(candidates) == {
        Path("cli/helix-codex"),
        Path("cli/lib/allowed_files_estimator.py"),
        Path("cli/lib/tests/test_allowed_files_estimator.py"),
    }
    assert confidence >= 0.5
    assert low_confidence is False


def test_low_confidence_fallback(tmp_path: Path) -> None:
    repo_root = create_repo_fixture(tmp_path)

    candidates, confidence, low_confidence = allowed_files_estimator.estimate_allowed_files(
        "Improve runtime quality",
        repo_root,
    )

    assert candidates == []
    assert confidence < 0.5
    assert low_confidence is True


def test_false_positive_avoidance(tmp_path: Path) -> None:
    repo_root = create_repo_fixture(tmp_path)
    task = "Update cli/lib/allowed_files_estimator.py scoring"

    candidates, confidence, low_confidence = allowed_files_estimator.estimate_allowed_files(
        task,
        repo_root,
    )

    assert Path("cli/lib/allowed_files_estimator.py") in candidates
    assert Path("docs/allowed_files_notes.md") not in candidates
    assert confidence >= 0.5
    assert low_confidence is False


def test_low_confidence_still_returns_suggestions_from_find_matching_files(tmp_path: Path) -> None:
    repo_root = create_repo_fixture(tmp_path)

    suggestions = allowed_files_estimator.find_matching_files(
        allowed_files_estimator.extract_keywords("allowed files notes"),
        repo_root,
    )

    assert Path("docs/allowed_files_notes.md") in suggestions
