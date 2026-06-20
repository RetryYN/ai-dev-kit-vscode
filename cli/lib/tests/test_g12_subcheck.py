from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import g12_subcheck


REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_AT_IDS = [f"AT-{index:02d}" for index in range(1, 58)]
ANCHORED_AT_IDS = ["AT-17", "AT-29", "AT-30", "AT-50", "AT-53"]


def test_load_at_inventory_reads_expected_57_at_ids() -> None:
    inventory = g12_subcheck.load_at_inventory(REPO_ROOT)

    assert sorted(inventory) == EXPECTED_AT_IDS
    assert len(inventory) == 57
    assert inventory["AT-01"]["doc_path"] == g12_subcheck.L12_TEST_DESIGN_PATH.as_posix()


def test_collect_g12_subcheck_counts_real_repo_inventory_when_skip_exec() -> None:
    report = g12_subcheck.collect_g12_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["implemented"] is True
    assert report["passed"] is False
    assert report["at_total"] == 57
    assert report["gap_count"] == 52
    assert report["anchored"]["ids"] == ANCHORED_AT_IDS
    assert report["anchored"]["count"] == 5
    assert report["exec_pass"]["count"] == 5
    assert report["missing"]["count"] == 52
    assert report["unanchored_but_exists"]["count"] == 0


def test_collect_g12_subcheck_detects_markerless_anchor_as_unanchored(monkeypatch) -> None:
    broken_map = dict(g12_subcheck.G12_ANCHOR_MAP)
    broken_map["AT-17"] = ["cli/tests/test-helix-gate-readiness.bats::AT-99"]
    monkeypatch.setattr(g12_subcheck, "G12_ANCHOR_MAP", broken_map)

    report = g12_subcheck.collect_g12_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["anchored"]["count"] == 4
    assert report["missing"]["count"] == 52
    assert report["unanchored_but_exists"]["ids"] == ["AT-17"]
    assert report["exec_pass"]["count"] == 4


def test_collect_g12_subcheck_rejects_anchor_without_explicit_needle(monkeypatch) -> None:
    broken_map = dict(g12_subcheck.G12_ANCHOR_MAP)
    broken_map["AT-17"] = ["cli/tests/test-helix-gate-readiness.bats"]
    monkeypatch.setattr(g12_subcheck, "G12_ANCHOR_MAP", broken_map)

    report = g12_subcheck.collect_g12_subcheck(REPO_ROOT, execute_g7_tests=False)

    assert report["anchored"]["count"] == 4
    assert report["missing"]["count"] == 52
    assert report["unanchored_but_exists"]["ids"] == ["AT-17"]
    assert report["exec_pass"]["count"] == 4


def test_collect_g12_subcheck_execution_gating_tracks_runner_failures() -> None:
    def fake_runner(_root: Path, rel_path: str) -> dict[str, object]:
        return {"returncode": 1 if rel_path == "cli/tests/test-helix-codex.bats" else 0}

    report = g12_subcheck.collect_g12_subcheck(
        REPO_ROOT,
        execute_g7_tests=True,
        test_runner=fake_runner,
    )

    assert report["anchored"]["count"] == 5
    assert report["exec_pass"]["count"] == 4
    assert report["passed"] is False


def test_existing_anchor_paths_rejects_substring_only_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: AT-170\n", encoding="utf-8")

    assert g12_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::AT-17"],
    ) == []


def test_existing_anchor_paths_accepts_word_boundary_match(tmp_path: Path) -> None:
    test_file = tmp_path / "cli/lib/tests/test_anchor_fixture.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("anchor candidate: AT-17 |\n", encoding="utf-8")

    assert g12_subcheck._existing_anchor_paths(
        tmp_path,
        ["cli/lib/tests/test_anchor_fixture.py::AT-17"],
    ) == ["cli/lib/tests/test_anchor_fixture.py"]


def test_render_text_surfaces_implemented_passed_and_gap_count() -> None:
    report = g12_subcheck.collect_g12_subcheck(REPO_ROOT, execute_g7_tests=False)
    rendered = g12_subcheck.render_text(report)

    assert "implemented: true" in rendered
    assert "passed: false" in rendered
    assert "gap_count: 52" in rendered


def test_check_g12_subcheck_json_reports_real_repo_inventory() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor"), "check_g12_subcheck", "--json"],
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
    assert payload["at_total"] == 57
    assert payload["anchored"]["count"] == 5
    assert payload["missing"]["count"] == 52


def test_check_g12_subcheck_gate_fails_while_g12_remains_deferred() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor"), "check_g12_subcheck", "--gate", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert payload["gap_count"] == 52


def test_python_module_g12_subcheck_supports_json_output() -> None:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(REPO_ROOT), "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "cli.lib.g12_subcheck", "--json"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["implemented"] is True
    assert payload["at_total"] == 57
    assert payload["anchored"]["count"] == 5
