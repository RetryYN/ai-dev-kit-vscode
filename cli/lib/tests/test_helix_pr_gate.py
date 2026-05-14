from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _copy_tool_cli(tmp_path: Path) -> Path:
    tool_root = tmp_path / "tool"
    shutil.copytree(REPO_ROOT / "cli", tool_root / "cli")
    return tool_root


def _init_git_repo(project_root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=project_root, check=True)
    (project_root / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: base"], cwd=project_root, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=project_root, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feature/pr-gate"], cwd=project_root, check=True)
    (project_root / "README.md").write_text("base\nchange\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: add pr gate"], cwd=project_root, check=True)
    (project_root / ".helix").mkdir(parents=True, exist_ok=True)


def _write_mock_gh(bin_dir: Path, log_path: Path) -> None:
    (bin_dir / "gh").write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$*\" >> '{log_path}'\n"
        "exit 0\n",
        encoding="utf-8",
    )
    (bin_dir / "gh").chmod(0o755)


def _run_pr(
    tool_root: Path,
    project_root: Path,
    bin_dir: Path,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(tool_root)
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    env["HOME"] = str(project_root / "home")
    env["HELIX_DISABLE_FEEDBACK"] = "1"
    env["PATH"] = f"{bin_dir}:{Path('/usr/bin')}:{Path('/bin')}"
    if extra_env:
        env.update(extra_env)
    (project_root / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [str(tool_root / "cli" / "helix-pr"), *args],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_pr_gate_imports_push_gate_module(tmp_path: Path) -> None:
    tool_root = _copy_tool_cli(tmp_path)
    project_root = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    project_root.mkdir()
    bin_dir.mkdir()
    _init_git_repo(project_root)
    _write_mock_gh(bin_dir, tmp_path / "gh.log")

    marker = tmp_path / "imported.log"
    (tool_root / "cli" / "lib" / "push_gate.py").write_text(
        "from pathlib import Path\n"
        "import os\n\n"
        "def run_all_gates(execute=False, remote='origin', branch='main'):\n"
        "    Path(os.environ['PR_GATE_LOG']).write_text('imported\\n', encoding='utf-8')\n"
        "    return {'ok': True, 'execute_requested': execute, 'remote': remote, 'branch': branch}\n",
        encoding="utf-8",
    )

    completed = _run_pr(
        tool_root,
        project_root,
        bin_dir,
        "--gate",
        "--dry-run",
        extra_env={"PR_GATE_LOG": str(marker)},
    )

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert marker.read_text(encoding="utf-8") == "imported\n"
    assert "Gate validation: passed" in output
    assert "PR creation skipped" in output


def test_pr_auto_merge_flag_parses(tmp_path: Path) -> None:
    tool_root = _copy_tool_cli(tmp_path)
    project_root = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    project_root.mkdir()
    bin_dir.mkdir()
    _init_git_repo(project_root)

    gh_log = tmp_path / "gh.log"
    _write_mock_gh(bin_dir, gh_log)
    (tool_root / "cli" / "lib" / "push_gate.py").write_text(
        "def run_all_gates(execute=False, remote='origin', branch='main'):\n"
        "    return {'ok': True, 'execute_requested': execute, 'remote': remote, 'branch': branch}\n",
        encoding="utf-8",
    )

    completed = _run_pr(tool_root, project_root, bin_dir, "--gate", "--auto-merge")

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    commands = gh_log.read_text(encoding="utf-8")
    assert "pr create" in commands
    assert "pr merge --squash" in commands
