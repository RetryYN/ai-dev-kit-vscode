from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _copy_tool_cli(tmp_path: Path) -> Path:
    tool_root = tmp_path / "tool"
    shutil.copytree(REPO_ROOT / "cli", tool_root / "cli")
    return tool_root


def _run_innovation(tool_root: Path, project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(tool_root)
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    env["HOME"] = str(project_root / "home")
    (project_root / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [str(tool_root / "cli" / "helix-innovation"), *args],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_innovation_subcommand_parsing(tmp_path: Path) -> None:
    tool_root = _copy_tool_cli(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)

    completed = _run_innovation(tool_root, project_root, "tech", "--task", "DORA 指標を国内向けに翻案")

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "[helix innovation] tech subagent prompt 生成完了" in output
    assert 'subagent_type: "pdm-tech-innovation"' in output


def test_team_yaml_parse() -> None:
    payload = yaml.safe_load((REPO_ROOT / "cli" / "templates" / "teams" / "innovation-team.yaml").read_text(encoding="utf-8"))

    assert payload["team_name"] == "pdm-innovation-team"
    assert payload["parallel_stage"][0]["role"] == "pdm-tech-innovation"
    assert payload["parallel_stage"][2]["role"] == "pmo-tech-docs"
    assert payload["serial_stage"][-1]["role"] == "pdm-innovation-manager"
    assert any(member["role"] == "pdm-innovation-manager" for member in payload["members"])
