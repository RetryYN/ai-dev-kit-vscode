from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db  # noqa: E402
from detectors import registry  # noqa: E402


def _script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "helix-detect"


def test_list_detectors_returns_fifteen_axes_in_order() -> None:
    detectors = registry.list_detectors()

    assert len(detectors) == 15
    assert [item["axis_id"] for item in detectors] == [f"axis-{idx:02d}" for idx in range(15)]
    assert detectors[0]["kind"] == "baseline"
    assert detectors[-1]["axis_id"] == "axis-14"
    axis_kinds = {item["axis_id"]: item["kind"] for item in detectors}
    assert axis_kinds["axis-04"] == "detector"
    assert axis_kinds["axis-05"] == "detector"
    assert axis_kinds["axis-06"] == "detector"
    assert axis_kinds["axis-03"] == "detector"
    assert axis_kinds["axis-09"] == "detector"
    assert axis_kinds["axis-10"] == "detector"
    assert axis_kinds["axis-11"] == "detector"
    assert axis_kinds["axis-07"] == "detector"
    assert axis_kinds["axis-08"] == "detector"
    assert axis_kinds["axis-12"] == "detector"
    assert axis_kinds["axis-13"] == "detector"
    assert axis_kinds["axis-14"] == "detector"


def test_run_detector_axis_00_returns_blocked_stub_and_records_run(tmp_path: Path) -> None:
    db_path = tmp_path / ".helix" / "helix.db"

    result = registry.run_detector("axis-00", db_path)

    assert result.verdict == "blocked"
    assert result.raw["reason"] == "not_implemented yet, see PLAN-063 W-3〜W-9"
    assert result.raw["baseline"] is True

    conn = helix_db.get_connection(db_path)
    try:
        rows = conn.execute("SELECT axis_id, verdict, raw_json FROM detector_runs ORDER BY run_id").fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert rows[0]["axis_id"] == "axis-00"
    assert rows[0]["verdict"] == "blocked"
    assert "not_implemented yet" in rows[0]["raw_json"]


def test_dashboard_data_returns_dict_with_each_axis_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    project_root = tmp_path / "project"
    (project_root / "skills").mkdir(parents=True, exist_ok=True)
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "cli" / "lib").mkdir(parents=True, exist_ok=True)
    (project_root / "skills" / "SKILL_MAP.md").write_text("# SKILL_MAP\n", encoding="utf-8")
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    data = registry.dashboard_data(db_path)

    assert isinstance(data, dict)
    assert data["total"] == 15
    assert data["counts"]["passed"] == 1
    assert data["counts"]["blocked"] == 14
    assert data["axes"][0]["axis_id"] == "axis-00"
    assert any(axis["axis_id"] == "axis-10" and axis["verdict"] == "passed" for axis in data["axes"])
    assert all("verdict" in axis for axis in data["axes"])
    assert "graph TD" in data["mermaid"]


def test_cli_list_outputs_all_axes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project_root, check=True)
    (project_root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project_root, check=True)

    env = {
        "HOME": str(tmp_path / "home"),
        "HELIX_PROJECT_ROOT": str(project_root),
        "HELIX_HOME": str(Path(__file__).resolve().parents[3]),
    }
    (tmp_path / "home").mkdir()

    completed = subprocess.run(
        [str(_script_path()), "list"],
        cwd=project_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "axis-00" in completed.stdout
    assert "axis-14" in completed.stdout


def test_cli_run_axis_00_json_outputs_stub_state(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project_root, check=True)
    (project_root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project_root, check=True)
    (tmp_path / "home").mkdir()

    env = {
        "HOME": str(tmp_path / "home"),
        "HELIX_PROJECT_ROOT": str(project_root),
        "HELIX_HOME": str(Path(__file__).resolve().parents[3]),
    }

    completed = subprocess.run(
        [str(_script_path()), "run", "axis-00", "--json"],
        cwd=project_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["result"]["verdict"] == "blocked"
    assert payload["result"]["raw"]["baseline"] is True
