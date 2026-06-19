from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import g9_subcheck


REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_ST_IDS = [
    "ST-SYS-01",
    "ST-SYS-02",
    "ST-SYS-03",
    "ST-FR-01",
    "ST-FR-02",
    "ST-FR-03",
    "ST-FR-04",
    "ST-DATA-01",
    "ST-DATA-02",
    "ST-IF-01",
    "ST-IF-02",
    "ST-IF-03",
    "ST-IF-04",
    "ST-NFR-01",
    "ST-NFR-02",
    "ST-NFR-03",
    "ST-NEG-01",
    "ST-NEG-02",
]


def test_load_st_inventory_reads_expected_18_st_ids() -> None:
    inventory = g9_subcheck.load_st_inventory(REPO_ROOT)

    assert sorted(inventory) == sorted(EXPECTED_ST_IDS)
    assert len(inventory) == 18
    assert inventory["ST-SYS-01"]["doc_path"] == g9_subcheck.L9_TEST_DESIGN_PATH.as_posix()


def test_collect_g9_subcheck_counts_real_repo_inventory_when_skip_exec() -> None:
    report = g9_subcheck.collect_g9_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["implemented"] is True
    assert report["passed"] is False
    assert report["st_total"] == 18
    assert report["gap_count"] == 13
    assert report["anchored"]["ids"] == [
        "ST-IF-01",
        "ST-IF-02",
        "ST-IF-03",
        "ST-SYS-01",
        "ST-SYS-03",
    ]
    assert report["anchored"]["count"] == 5
    assert report["exec_pass"]["count"] == 5
    assert report["missing"]["count"] == 13
    assert report["unanchored_but_exists"]["count"] == 0


def test_collect_g9_subcheck_detects_markerless_anchor_as_unanchored(monkeypatch) -> None:
    broken_map = dict(g9_subcheck.G9_ANCHOR_MAP)
    broken_map["ST-SYS-01"] = ["cli/tests/test-helix-routing.bats::ST-SYS-99"]
    monkeypatch.setattr(g9_subcheck, "G9_ANCHOR_MAP", broken_map)

    report = g9_subcheck.collect_g9_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["anchored"]["count"] == 4
    assert report["missing"]["count"] == 13
    assert report["unanchored_but_exists"]["ids"] == ["ST-SYS-01"]
    assert report["exec_pass"]["count"] == 4


def test_collect_g9_subcheck_rejects_anchor_without_explicit_needle(monkeypatch) -> None:
    broken_map = dict(g9_subcheck.G9_ANCHOR_MAP)
    broken_map["ST-SYS-01"] = ["cli/tests/test-helix-routing.bats"]
    monkeypatch.setattr(g9_subcheck, "G9_ANCHOR_MAP", broken_map)

    report = g9_subcheck.collect_g9_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["anchored"]["count"] == 4
    assert report["missing"]["count"] == 13
    assert report["unanchored_but_exists"]["ids"] == ["ST-SYS-01"]
    assert report["exec_pass"]["count"] == 4


def test_collect_g9_subcheck_execution_gating_tracks_runner_failures() -> None:
    def fake_runner(_root: Path, rel_path: str) -> dict[str, object]:
        return {"returncode": 1 if rel_path == "cli/tests/test-helix-routing.bats" else 0}

    report = g9_subcheck.collect_g9_subcheck(
        REPO_ROOT,
        execute_g7_tests=True,
        test_runner=fake_runner,
    )

    assert report["anchored"]["count"] == 5
    assert report["exec_pass"]["count"] == 3
    assert report["passed"] is False


def test_existing_anchor_paths_rejects_substring_only_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: ST-IF-010\n", encoding="utf-8")

    assert g9_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::ST-IF-01"],
    ) == []


def test_existing_anchor_paths_accepts_word_boundary_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: ST-IF-01 |\n", encoding="utf-8")

    assert g9_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::ST-IF-01"],
    ) == ["cli/lib/tests/test_anchor_fixture.py"]


def test_render_text_surfaces_implemented_passed_and_gap_count() -> None:
    report = g9_subcheck.collect_g9_subcheck(REPO_ROOT, execute_g7_tests=False)
    rendered = g9_subcheck.render_text(report)

    assert "implemented: true" in rendered
    assert "passed: false" in rendered
    assert "gap_count: 13" in rendered


def test_check_g9_subcheck_json_reports_real_repo_inventory() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor"), "check_g9_subcheck", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["implemented"] is True
    assert payload["passed"] is False
    assert payload["st_total"] == 18
    assert payload["anchored"]["count"] == 5
    assert payload["missing"]["count"] == 13


def test_check_g9_subcheck_gate_fails_while_g9_remains_deferred() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor"), "check_g9_subcheck", "--gate", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert payload["gap_count"] == 13


def test_python_module_g9_subcheck_supports_json_output() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "cli.lib.g9_subcheck", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["implemented"] is True
    assert payload["st_total"] == 18
    assert payload["anchored"]["count"] == 5
