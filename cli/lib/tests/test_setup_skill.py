import os
import subprocess
import sys
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import setup_helper

CLI = REPO_ROOT / "cli" / "helix-setup"


def _write_component(setup_dir: Path, name: str) -> Path:
    path = setup_dir / f"{name}.sh"
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
state_file="${HELIX_PROJECT_ROOT}/.state-${COMPONENT_NAME:-dummy}"
describe() { echo "${COMPONENT_NAME:-dummy} component"; }
verify() {
  if [[ -f "$state_file" ]]; then
    echo "installed"
    return 0
  fi
  echo "missing" >&2
  return 1
}
install() {
  mkdir -p "$(dirname "$state_file")"
  if [[ -f "$state_file" ]]; then
    echo "already installed"
    return 0
  fi
  echo "installed" >"$state_file"
  echo "installed"
  return 0
}
repair() {
  if [[ -f "$state_file" ]]; then
    echo "repair not needed"
    return 3
  fi
  install
}
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _component(tmp_path: Path, name: str = "dummy") -> tuple[setup_helper.Component, Path]:
    project = tmp_path / "project"
    setup_dir = tmp_path / "setup"
    project.mkdir()
    setup_dir.mkdir()
    path = _write_component(setup_dir, name)
    return setup_helper.Component(name=name, path=path, project_root=project), project


def _run_setup(project: Path, setup_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    return subprocess.run(
        [str(CLI), *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_verify_returns_correct_exit_code(tmp_path: Path) -> None:
    component, project = _component(tmp_path)
    assert component.verify().returncode == 1
    (project / ".state-dummy").write_text("installed\n", encoding="utf-8")
    assert component.verify().returncode == 0


def test_install_idempotent(tmp_path: Path) -> None:
    component, project = _component(tmp_path)
    assert component.install().returncode == 0
    assert (project / ".state-dummy").exists()
    second = component.install()
    assert second.returncode == 0
    assert "already installed" in second.stdout


def test_repair_idempotent(tmp_path: Path) -> None:
    component, _project = _component(tmp_path)
    assert component.repair().returncode == 0
    second = component.repair()
    assert second.returncode == 3
    assert "repair not needed" in second.stdout


def test_list_shows_all_components(tmp_path: Path) -> None:
    project = tmp_path / "project"
    setup_dir = tmp_path / "setup"
    project.mkdir()
    setup_dir.mkdir()
    _write_component(setup_dir, "alpha")
    _write_component(setup_dir, "beta")
    components = setup_helper.discover_components(setup_dir, project_root=project)
    table = setup_helper.format_component_list(components)
    assert "name\tdescription" in table
    assert "alpha\t" in table
    assert "beta\t" in table


def test_status_per_component(tmp_path: Path) -> None:
    component, project = _component(tmp_path, "status-one")
    setup_dir = component.path.parent
    components = setup_helper.discover_components(setup_dir, project_root=project)
    table = setup_helper.format_status_table([setup_helper.find_component(components, "status-one")])
    assert "name\tstatus\tdescription" in table
    assert "status-one\tneeds_attention\t" in table


def test_unknown_component_errors_with_2(tmp_path: Path) -> None:
    project = tmp_path / "project"
    setup_dir = tmp_path / "setup"
    project.mkdir()
    setup_dir.mkdir()
    result = _run_setup(project, setup_dir, "verify", "--name", "missing")
    assert result.returncode == 2
    assert "unknown component: missing" in result.stderr


def test_sample_redaction_denylist_install_creates_template(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    result = subprocess.run(
        [str(CLI), "install", "--name", "redaction-denylist"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    template = project / ".helix" / "audit" / "redaction-denylist.example.yaml"
    assert template.exists()
    assert "generic_api_key" in template.read_text(encoding="utf-8")
