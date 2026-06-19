from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import g8_subcheck


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCTOR = REPO_ROOT / "cli/helix-doctor"


def _run_doctor(project_root: Path, *args: str, skip_exec: bool = True) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(project_root)}
    if skip_exec:
        env["HELIX_DOCTOR_SKIP_EXEC_TESTS"] = "1"
    return subprocess.run(
        [str(DOCTOR), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_collect_g8_subcheck_uses_it_only_inventory() -> None:
    report = g8_subcheck.collect_g8_subcheck(REPO_ROOT, execute_tests=False)

    all_ids = (
        report["anchored"]["ids"]
        + report["missing"]["ids"]
        + report["unanchored_but_exists"]["ids"]
    )
    assert report["it_total"] == 21
    assert len(all_ids) == 21
    assert all(item.startswith("IT-") for item in all_ids)
    assert not any(item.startswith(("UT-", "RD-UT-", "DGA-UT-", "EGA-UT-")) for item in all_ids)


def test_collect_g8_subcheck_counts_real_repo_inventory_when_skip_exec() -> None:
    report = g8_subcheck.collect_g8_subcheck(REPO_ROOT, execute_tests=False)

    assert report["it_total"] == 21
    assert report["anchored"]["count"] == 21
    assert report["missing"]["count"] == 0
    assert report["unanchored_but_exists"]["count"] == 0
    assert report["exec_pass"]["count"] == 21


def test_collect_g8_subcheck_detects_markerless_passing_file_as_unanchored(monkeypatch) -> None:
    broken_map = dict(g8_subcheck.G8_ANCHOR_MAP)
    broken_map["IT-MOD-06"] = ["cli/lib/tests/test_workspace_manager.py::IT-MOD-06"]
    monkeypatch.setattr(g8_subcheck, "G8_ANCHOR_MAP", broken_map)

    report = g8_subcheck.collect_g8_subcheck(REPO_ROOT, execute_tests=False)

    assert report["it_total"] == 21
    assert report["anchored"]["count"] == 20
    assert report["missing"]["ids"] == []
    assert report["unanchored_but_exists"]["ids"] == ["IT-MOD-06"]
    assert report["exec_pass"]["count"] == 20


def test_collect_g8_subcheck_rejects_anchor_without_explicit_needle(monkeypatch) -> None:
    broken_map = dict(g8_subcheck.G8_ANCHOR_MAP)
    broken_map["IT-MOD-06"] = ["cli/lib/tests/test_integration_l45.py"]
    monkeypatch.setattr(g8_subcheck, "G8_ANCHOR_MAP", broken_map)

    report = g8_subcheck.collect_g8_subcheck(REPO_ROOT, execute_tests=False)

    assert report["anchored"]["count"] == 20
    assert report["missing"]["count"] == 0
    assert report["unanchored_but_exists"]["ids"] == ["IT-MOD-06"]
    assert report["exec_pass"]["count"] == 20


def test_collect_g8_subcheck_accepts_marker_backed_anchor() -> None:
    assert g8_subcheck._existing_anchor_paths(
        REPO_ROOT,
        ["cli/lib/tests/test_integration_l45.py::IT-MOD-06"],
    ) == ["cli/lib/tests/test_integration_l45.py"]


def test_existing_anchor_paths_rejects_substring_only_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: IT-DB-030\n", encoding="utf-8")

    assert g8_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::IT-DB-03"],
    ) == []


def test_existing_anchor_paths_accepts_word_boundary_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: IT-DB-03 |\n", encoding="utf-8")

    assert g8_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::IT-DB-03"],
    ) == ["cli/lib/tests/test_anchor_fixture.py"]


def test_check_g8_subcheck_gate_passes_with_structural_skip_exec() -> None:
    result = _run_doctor(REPO_ROOT, "check_g8_subcheck", "--gate", "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["it_total"] == 21
    assert payload["anchored"]["count"] == 21
    assert payload["exec_pass"]["count"] == 21
    assert payload["missing"]["count"] == 0
    assert payload["unanchored_but_exists"]["count"] == 0


def test_check_g8_subcheck_json_is_it_only_inventory() -> None:
    result = _run_doctor(REPO_ROOT, "check_g8_subcheck", "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    all_ids = (
        payload["anchored"]["ids"]
        + payload["missing"]["ids"]
        + payload["unanchored_but_exists"]["ids"]
    )
    assert payload["it_total"] == 21
    assert all(item.startswith("IT-") for item in all_ids)


def test_python_module_g8_subcheck_supports_json_output() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "cli.lib.g8_subcheck", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["it_total"] == 21
    assert payload["anchored"]["count"] == 21
    assert payload["exec_pass"]["count"] == 21
