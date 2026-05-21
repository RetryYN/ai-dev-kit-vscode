from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import sprint_auto_check


def test_run_py_compile_valid(tmp_path: Path) -> None:
    target = tmp_path / "ok.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    result = sprint_auto_check.run_py_compile([target.as_posix()])

    assert result["status"] == "pass"
    assert result["files_checked"] == 1


def test_run_py_compile_invalid(tmp_path: Path) -> None:
    target = tmp_path / "broken.py"
    target.write_text("def broken(:\n    pass\n", encoding="utf-8")

    result = sprint_auto_check.run_py_compile([target.as_posix()])

    assert result["status"] == "fail"
    assert result["errors"]


def test_run_pytest_empty_paths() -> None:
    result = sprint_auto_check.run_pytest([])

    assert result["failed"] == 0
    assert "no target paths" in result["errors"]


def test_auto_check_returns_dict(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "ok.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    monkeypatch.setattr(
        sprint_auto_check,
        "run_full_suite",
        lambda: {"status": "skip", "pytest_passed": 0, "bats_passed": 0, "errors": []},
    )
    monkeypatch.setattr(
        sprint_auto_check,
        "run_pytest",
        lambda target_paths: {"passed": 1, "failed": 0, "errors": [], "duration_sec": 0.01},
    )

    result = sprint_auto_check.auto_check("SPRINT-1", [target.as_posix()])

    assert isinstance(result, dict)
    assert isinstance(result["overall_pass"], bool)
