from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import g14_subcheck


REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_OT_IDS = [f"OT-{index:02d}" for index in range(1, 21)]
ANCHORED_OT_IDS = ["OT-20"]


def test_load_ot_inventory_reads_expected_20_ot_ids() -> None:
    inventory = g14_subcheck.load_ot_inventory(REPO_ROOT)

    assert sorted(inventory) == EXPECTED_OT_IDS
    assert len(inventory) == 20
    assert inventory["OT-01"]["doc_path"] == g14_subcheck.L14_TEST_DESIGN_PATH.as_posix()


def test_collect_g14_subcheck_counts_real_repo_inventory_when_skip_exec() -> None:
    report = g14_subcheck.collect_g14_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["implemented"] is True
    assert report["passed"] is False
    assert report["ot_total"] == 20
    assert report["gap_count"] == 19
    assert report["anchored"]["ids"] == ANCHORED_OT_IDS
    assert report["anchored"]["count"] == 1
    assert report["exec_pass"]["count"] == 1
    assert report["missing"]["count"] == 19
    assert report["unanchored_but_exists"]["count"] == 0


def test_collect_g14_subcheck_detects_markerless_anchor_as_unanchored(monkeypatch) -> None:
    broken_map = dict(g14_subcheck.G14_ANCHOR_MAP)
    broken_map["OT-18"] = ["cli/tests/test-helix-routing.bats::OT-99"]
    monkeypatch.setattr(g14_subcheck, "G14_ANCHOR_MAP", broken_map)

    report = g14_subcheck.collect_g14_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["anchored"]["count"] == 1
    assert report["missing"]["count"] == 18
    assert report["unanchored_but_exists"]["ids"] == ["OT-18"]
    assert report["exec_pass"]["count"] == 1


def test_collect_g14_subcheck_rejects_anchor_without_explicit_needle(monkeypatch) -> None:
    broken_map = dict(g14_subcheck.G14_ANCHOR_MAP)
    broken_map["OT-18"] = ["cli/tests/test-helix-routing.bats"]
    monkeypatch.setattr(g14_subcheck, "G14_ANCHOR_MAP", broken_map)

    report = g14_subcheck.collect_g14_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["anchored"]["count"] == 1
    assert report["missing"]["count"] == 18
    assert report["unanchored_but_exists"]["ids"] == ["OT-18"]
    assert report["exec_pass"]["count"] == 1


def test_collect_g14_subcheck_execution_gating_tracks_runner_failures() -> None:
    def fake_runner(_root: Path, rel_path: str) -> dict[str, object]:
        return {"returncode": 1 if rel_path == "cli/tests/test-handover.bats" else 0}

    report = g14_subcheck.collect_g14_subcheck(
        REPO_ROOT,
        execute_g7_tests=True,
        test_runner=fake_runner,
    )

    assert report["anchored"]["count"] == 1
    assert report["exec_pass"]["count"] == 0
    assert report["passed"] is False


def test_existing_anchor_paths_rejects_substring_only_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: OT-180\n", encoding="utf-8")

    assert g14_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::OT-18"],
    ) == []


def test_existing_anchor_paths_accepts_word_boundary_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: OT-18 |\n", encoding="utf-8")

    assert g14_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::OT-18"],
    ) == ["cli/lib/tests/test_anchor_fixture.py"]


def test_render_text_surfaces_implemented_passed_and_gap_count() -> None:
    report = g14_subcheck.collect_g14_subcheck(REPO_ROOT, execute_g7_tests=False)
    rendered = g14_subcheck.render_text(report)

    assert "implemented: true" in rendered
    assert "passed: false" in rendered
    assert "gap_count: 19" in rendered


def test_check_g14_subcheck_json_reports_real_repo_inventory() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor"), "check_g14_subcheck", "--json"],
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
    assert payload["ot_total"] == 20
    assert payload["anchored"]["count"] == 1
    assert payload["missing"]["count"] == 19


def test_check_g14_subcheck_gate_fails_while_g14_remains_deferred() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor"), "check_g14_subcheck", "--gate", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert payload["gap_count"] == 19


def test_python_module_g14_subcheck_supports_json_output() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "cli.lib.g14_subcheck", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["implemented"] is True
    assert payload["ot_total"] == 20
    assert payload["anchored"]["count"] == 1
