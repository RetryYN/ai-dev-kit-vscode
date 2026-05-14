from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HELIX_BIN = REPO_ROOT / "cli" / "helix"


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=project, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=project, check=True, capture_output=True, text=True)
    (project / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project, check=True, capture_output=True, text=True)
    return project


def _run(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(project),
            "HOME": str(project / "home"),
        }
    )
    (project / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [str(HELIX_BIN), "vmodel", *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_helix_vmodel_list_json(tmp_path: Path) -> None:
    project = _init_project(tmp_path)

    proc = _run(project, "list", "--json")

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["drives"] == ["be", "fe", "db", "fullstack"]
    assert payload["layers"] == ["planning", "requirement", "architecture", "detailed", "functional"]


def test_helix_vmodel_show_plain_text(tmp_path: Path) -> None:
    project = _init_project(tmp_path)

    proc = _run(project, "show", "be", "planning")

    assert proc.returncode == 0, proc.stderr
    assert "drive: be" in proc.stdout
    assert "layer: planning" in proc.stdout
    assert "design.review_unit: plan" in proc.stdout
    assert "test.test_level: operational" in proc.stdout


def test_helix_vmodel_validate_plain_text(tmp_path: Path) -> None:
    project = _init_project(tmp_path)

    proc = _run(project, "validate")

    assert proc.returncode == 0, proc.stderr
    assert "VALIDATION: OK" in proc.stdout
    assert "config_path:" in proc.stdout


def test_helix_vmodel_show_invalid_drive(tmp_path: Path) -> None:
    project = _init_project(tmp_path)

    proc = _run(project, "show", "invalid", "planning")

    assert proc.returncode == 2
    assert "unknown drive: invalid" in proc.stderr
