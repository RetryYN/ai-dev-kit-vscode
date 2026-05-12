from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import helix_db
from detectors.axis_08_plan_integrity import Axis08PlanIntegrity


def _write_plan(root: Path, *, status: str, plan_id: str) -> None:
    plan_path = root / "docs" / "plans" / f"{plan_id}-sample.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "---\n"
        f"plan_id: {plan_id}\n"
        f"status: {status}\n"
        "---\n"
        "# sample plan\n",
        encoding="utf-8",
    )


def _fake_git_run(expected_calls: list[list[str]]):
    def runner(command, check, capture_output, text, cwd):  # type: ignore[no-untyped-def]
        expected_calls.append(command)
        return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    return runner


def test_axis_08_reports_no_commits_and_no_retro_for_finalized_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_plan(project_root, status="finalized", plan_id="PLAN-101")
    db_path = project_root / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    calls: list[list[str]] = []
    monkeypatch.setattr("detectors.axis_08_plan_integrity.subprocess.run", _fake_git_run(calls))

    result = Axis08PlanIntegrity().run(db_path)

    assert result.verdict == "failed"
    kinds = {finding["kind"] for finding in result.findings}
    assert {"no_commits", "no_retro"} <= kinds
    assert any("PLAN-101" in " ".join(command) for command in calls)


def test_axis_08_relaxes_draft_plans_to_warning_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_plan(project_root, status="draft", plan_id="PLAN-102")
    db_path = project_root / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    monkeypatch.setattr("detectors.axis_08_plan_integrity.subprocess.run", _fake_git_run([]))

    result = Axis08PlanIntegrity().run(db_path)

    assert result.verdict == "passed"
    assert result.findings == [{"plan_id": "PLAN-102", "status": "draft", "kind": "stale_draft"}]
