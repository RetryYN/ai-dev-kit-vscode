from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import anchor_quality


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCTOR = REPO_ROOT / "cli" / "helix-doctor"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_assess_anchor_accepts_non_trivial_python_assert(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
## ST-SYS-01
def test_real_assert():
    value = 2 + 2
    assert value == 4
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result["genuine"] is True
    assert result["reason"] == "python_assertion_detected"


def test_assess_anchor_accepts_pytest_raises(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
import pytest

## ST-SYS-01
def test_raises():
    with pytest.raises(ValueError):
        raise ValueError("boom")
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result["genuine"] is True
    assert result["reason"] == "python_pytest_raises_detected"


def test_assess_anchor_rejects_trivial_assert_true(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
## ST-SYS-01
def test_trivial():
    assert True
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result == {"genuine": False, "reason": "python_trivial_assert_only"}


def test_assess_anchor_rejects_pass_only(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
## ST-SYS-01
def test_pass_only():
    pass
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result == {"genuine": False, "reason": "python_pass_only"}


def test_assess_anchor_rejects_marker_only_comment(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
## ST-SYS-01

def test_other():
    assert 1 == 1
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result == {"genuine": False, "reason": "python_marker_only"}


def test_assess_anchor_rejects_skip_only(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
import pytest

## ST-SYS-01
@pytest.mark.skip(reason="not now")
def test_skipped():
    assert 2 == 2
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result == {"genuine": False, "reason": "python_skip_or_xfail"}


def test_assess_anchor_rejects_xfail_only(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
import pytest

## ST-SYS-01
@pytest.mark.xfail(reason="known failure")
def test_xfail():
    assert 2 == 3
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result == {"genuine": False, "reason": "python_skip_or_xfail"}


def test_assess_anchor_accepts_bats_status_check(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.bats",
        """
# ST-SYS-01
@test "checks status" {
  run echo ok
  [ "$status" -eq 0 ]
}
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result["genuine"] is True
    assert result["reason"] == "bats_assertion_detected"


def test_assess_anchor_rejects_bats_run_without_checks(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.bats",
        """
# ST-SYS-01
@test "run only" {
  run echo ok
}
""".strip()
        + "\n",
    )

    result = anchor_quality.assess_anchor(test_file, "ST-SYS-01")

    assert result == {"genuine": False, "reason": "bats_run_without_checks"}


def test_collect_anchor_quality_reports_weak_anchor_and_fails_gate(tmp_path: Path) -> None:
    test_file = _write(
        tmp_path / "tests/test_sample.py",
        """
## ST-SYS-01
def test_trivial():
    assert True
""".strip()
        + "\n",
    )

    report = anchor_quality.collect_anchor_quality(
        tmp_path,
        subchecks={
            "G9": {
                "anchor_map_ref": "tmp::G9_ANCHOR_MAP",
                "anchors": {"ST-SYS-01": [f"tests/test_sample.py::ST-SYS-01"]},
            }
        },
    )

    assert report["passed"] is False
    assert report["weak_anchor_count"] == 1
    assert report["severity_counts"] == {"P0": 1, "P1": 0}
    assert report["findings"][0]["gate"] == "G9"
    assert report["findings"][0]["severity"] == "P0"
    assert report["findings"][0]["reason"] == "python_trivial_assert_only"
    assert report["per_gate"]["G9"]["weak_ids"] == ["ST-SYS-01"]


def test_anchor_quality_avoids_static_subcheck_imports() -> None:
    tree = ast.parse((LIB_DIR / "anchor_quality.py").read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert imported_modules.isdisjoint(
        {"g7_subcheck", "g8_subcheck", "g9_subcheck", "g12_subcheck", "g14_subcheck"}
    )


def test_collect_anchor_quality_real_repo_is_clean() -> None:
    report = anchor_quality.collect_anchor_quality(REPO_ROOT)

    assert report["passed"] is True
    assert report["weak_anchor_count"] == 0
    assert report["severity_counts"] == {"P0": 0, "P1": 0}
    assert {"G7", "G8", "G9", "G12", "G14"} <= set(report["per_gate"])


def test_helix_doctor_check_anchor_quality_gate_json_passes_on_real_repo() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(DOCTOR), "check_anchor_quality", "--gate", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["weak_anchor_count"] == 0
