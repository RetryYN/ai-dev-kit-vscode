import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _copy_tool_cli(tmp_path: Path) -> Path:
    tool_root = tmp_path / "tool"
    shutil.copytree(REPO_ROOT / "cli", tool_root / "cli")
    return tool_root


def test_helix_matrix_fresh_clone(tmp_path: Path) -> None:
    tool_root = _copy_tool_cli(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HELIX_HOME"] = str(tool_root)
    env["HELIX_PROJECT_ROOT"] = str(project_root)

    result = subprocess.run(
        [str(tool_root / "cli" / "helix-matrix"), "init"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (project_root / ".helix" / "rules" / "deliverables.yaml").exists()
    assert (project_root / ".helix" / "rules" / "naming.yaml").exists()
    assert (project_root / ".helix" / "rules" / "common-defs.yaml").exists()


def test_helix_init_monorepo(tmp_path: Path) -> None:
    tool_root = _copy_tool_cli(tmp_path)
    project_root = tmp_path / "project"
    (project_root / "packages" / "api" / ".git").mkdir(parents=True, exist_ok=True)
    (project_root / ".git").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HELIX_HOME"] = str(tool_root)

    result = subprocess.run(
        [
            "bash",
            str(tool_root / "cli" / "helix-init"),
            "--monorepo-package",
            "packages/api",
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (project_root / "packages" / "api" / ".helix").is_dir()
    assert (project_root / "packages" / "api" / ".helix" / "rules" / "deliverables.yaml").exists()
