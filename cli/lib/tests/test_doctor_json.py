"""Tests for helix-doctor --json output.

契約: docs/plans/L7/L7-helix-doctor-json-implplan.md §2.B §2.D
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .test_doctor_recovery_check import _write_recovery_plan
from .test_helix_doctor import _prepare_project_root
from .test_role_config_consistency import REPO_ROOT


def _run_doctor(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    env["HOME"] = str(project_root / "home")
    return subprocess.run(
        [str(REPO_ROOT / "cli/helix-doctor"), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _parse_doctor_json(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(result.stdout)


def _parse_text_summary(stdout: str) -> tuple[int, int, int]:
    match = re.search(r"結果:\s+(\d+)\s+pass,\s+(\d+)\s+fail,\s+(\d+)\s+warn", stdout)
    assert match is not None, stdout
    return tuple(int(value) for value in match.groups())


def test_doctor_json_returns_valid_json(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.D valid JSON."""
    _prepare_project_root(tmp_path)

    result = _run_doctor(tmp_path, "--json")

    assert result.returncode == 0
    payload = _parse_doctor_json(result)
    assert isinstance(payload, dict)


def test_doctor_json_schema_required_keys(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.A required keys."""
    _prepare_project_root(tmp_path)

    payload = _parse_doctor_json(_run_doctor(tmp_path, "--json"))

    for key in ("timestamp", "pass", "fail", "warn", "advisories", "summary"):
        assert key in payload


def test_doctor_json_advisories_structure(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.A advisory shape."""
    _prepare_project_root(tmp_path)

    payload = _parse_doctor_json(_run_doctor(tmp_path, "--json"))

    advisories = payload["advisories"]
    assert isinstance(advisories, list)
    assert advisories
    for advisory in advisories:
        assert isinstance(advisory, dict)
        for key in ("category", "name", "status", "detail"):
            assert key in advisory


def test_doctor_json_pass_count_matches_text(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.D summary parity."""
    _prepare_project_root(tmp_path)

    text_result = _run_doctor(tmp_path)
    json_result = _run_doctor(tmp_path, "--json")

    text_pass, text_fail, text_warn = _parse_text_summary(text_result.stdout)
    payload = _parse_doctor_json(json_result)

    assert payload["pass"] == text_pass
    assert payload["fail"] == text_fail
    assert payload["warn"] == text_warn


def test_doctor_json_does_not_affect_text_output(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.B text output unchanged."""
    _prepare_project_root(tmp_path)

    result = _run_doctor(tmp_path)

    assert result.returncode == 0
    assert "=== HELIX Doctor ===" in result.stdout
    assert "[必須依存]" in result.stdout
    assert "結果:" in result.stdout
    assert not result.stdout.lstrip().startswith("{")


def test_doctor_json_stdout_no_text_pollution(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.B stdout JSON only."""
    _prepare_project_root(tmp_path)

    result = _run_doctor(tmp_path, "--json")

    assert result.returncode == 0
    assert result.stdout.lstrip().startswith("{")
    assert "HELIX Doctor" not in result.stdout
    assert "[必須依存]" not in result.stdout
    assert "結果:" not in result.stdout


def test_doctor_json_fail_exits_with_1(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.B fail exit code parity."""
    _prepare_project_root(tmp_path)
    (tmp_path / ".helix" / "phase.yaml").unlink()

    text_result = _run_doctor(tmp_path)
    json_result = _run_doctor(tmp_path, "--json")

    assert text_result.returncode == 1
    assert json_result.returncode == 1
    payload = _parse_doctor_json(json_result)
    assert int(payload["fail"]) > 0


def test_doctor_json_with_max_age_days_parser(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.B parser order."""
    _prepare_project_root(tmp_path)

    first = _run_doctor(tmp_path, "--json", "--max-age-days", "7")
    second = _run_doctor(tmp_path, "--max-age-days", "7", "--json")

    assert first.returncode == 0
    assert second.returncode == 0
    assert isinstance(_parse_doctor_json(first), dict)
    assert isinstance(_parse_doctor_json(second), dict)


def test_doctor_check_recovery_plan_freshness_regression(tmp_path: Path) -> None:
    """DoD 検証: L7-helix-doctor-json-implplan.md §2.D recovery subcommand regression."""
    _prepare_project_root(tmp_path)
    docs_dir = tmp_path / "docs" / "plans"
    fresh_revised = (datetime.now(UTC) - timedelta(days=2)).date().isoformat()
    _write_recovery_plan(docs_dir / "PLAN-107-recovery-fresh.md", plan_id="PLAN-107", revised=fresh_revised)

    result = _run_doctor(tmp_path, "check_recovery_plan_freshness", "--max-age-days", "7")

    assert result.returncode == 0
    assert "✓ recovery plan freshness" in result.stdout
    assert "checked: 1" in result.stdout
