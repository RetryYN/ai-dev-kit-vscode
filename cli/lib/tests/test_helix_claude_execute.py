import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import handover


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=project, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=project, check=True, capture_output=True, text=True)
    (project / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project, check=True, capture_output=True, text=True)
    (project / ".helix").mkdir()
    (project / ".helix" / "phase.yaml").write_text(
        "project: pmo-test\ncurrent_phase: L4\nsprint:\n  current_step: .2\n",
        encoding="utf-8",
    )
    return project


def _write_role_conf(path: Path, *, model: str, thinking: str, permission: str, disallowed: str = "", allow_paths: str = "") -> None:
    lines = [
        f"claude_model={model}",
        f"claude_thinking={thinking}",
        f"claude_permission_mode={permission}",
    ]
    if disallowed:
        lines.append(f'claude_disallowed_tools="{disallowed}"')
    if allow_paths:
        lines.append(f'claude_allow_paths="{allow_paths}"')
    lines.extend(
        [
            "skills=(",
            ")",
            "common_docs=(",
            ")",
            'system_prompt="PMO"',
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _make_helix_home(tmp_path: Path) -> Path:
    helix_home = tmp_path / "helix-home"
    cli_dir = helix_home / "cli"
    cli_dir.mkdir(parents=True)
    for name in ("helix", "helix-claude", "claude"):
        (cli_dir / name).symlink_to(REPO_ROOT / "cli" / name)
    (cli_dir / "lib").symlink_to(REPO_ROOT / "cli" / "lib")
    (cli_dir / "templates").symlink_to(REPO_ROOT / "cli" / "templates")

    roles = cli_dir / "roles"
    roles.mkdir()
    _write_role_conf(
        roles / "pmo-sonnet.conf",
        model="claude-sonnet-4-6",
        thinking="medium",
        permission="plan",
        disallowed="Edit,Write,NotebookEdit",
    )
    _write_role_conf(
        roles / "pmo-haiku.conf",
        model="claude-haiku-4-5-20251001",
        thinking="low",
        permission="acceptEdits",
        allow_paths="docs/**,skills/**",
    )
    return helix_home


def _make_fake_claude(tmp_path: Path, exit_code: int = 0) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    args_file = tmp_path / "claude.args.json"
    script = bin_dir / "claude"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, os, sys, time",
                "sleep = float(os.environ.get('FAKE_CLAUDE_SLEEP', '0'))",
                "if sleep:",
                "    time.sleep(sleep)",
                f"open({str(args_file)!r}, 'w', encoding='utf-8').write(json.dumps(sys.argv[1:], ensure_ascii=False))",
                "print('fake claude ok')",
                f"sys.exit({exit_code})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir, args_file


def _run_claude(helix_home: Path, project: Path, bin_dir: Path, *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(helix_home),
            "HELIX_PROJECT_ROOT": str(project),
            "HOME": str(project / "home"),
            "PATH": f"{helix_home / 'cli'}:{bin_dir}:{env.get('PATH', '')}",
        }
    )
    if extra_env:
        env.update(extra_env)
    (project / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [str(helix_home / "cli" / "helix-claude"), *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _args_after(args: list[str], key: str) -> str:
    return args[args.index(key) + 1]


def test_helix_claude_execute_routes_sonnet(tmp_path: Path) -> None:
    project = _init_project(tmp_path)
    helix_home = _make_helix_home(tmp_path)
    bin_dir, args_file = _make_fake_claude(tmp_path)

    proc = _run_claude(
        helix_home,
        project,
        bin_dir,
        "--role",
        "pmo",
        "--model",
        "sonnet",
        "--task",
        "ping",
        "--execute",
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    args = json.loads(args_file.read_text(encoding="utf-8"))
    assert _args_after(args, "--model") == "claude-sonnet-4-6"
    assert _args_after(args, "--permission-mode") == "plan"
    assert _args_after(args, "--disallowedTools") == "Edit,Write,NotebookEdit"
    assert list((project / ".helix" / "cache" / "pmo").glob("*-758d61f2.log"))


def test_helix_claude_execute_routes_haiku_with_paths(tmp_path: Path) -> None:
    project = _init_project(tmp_path)
    helix_home = _make_helix_home(tmp_path)
    bin_dir, args_file = _make_fake_claude(tmp_path)

    proc = _run_claude(
        helix_home,
        project,
        bin_dir,
        "--role",
        "pmo",
        "--model",
        "haiku",
        "--task",
        "docs ping",
        "--execute",
        "--allow-paths",
        "docs/**",
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    args = json.loads(args_file.read_text(encoding="utf-8"))
    assert _args_after(args, "--model") == "claude-haiku-4-5-20251001"
    assert _args_after(args, "--permission-mode") == "acceptEdits"
    assert _args_after(args, "--disallowedTools") == ""
    assert "docs/**" in _args_after(args, "-p")


def test_helix_claude_execute_blocks_without_internal() -> None:
    proc = subprocess.run(
        [str(REPO_ROOT / "cli" / "claude"), "--print", "raw"],
        cwd=REPO_ROOT,
        env={k: v for k, v in os.environ.items() if not k.startswith("HELIX_CLAUDE_INTERNAL")},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 64
    assert "raw claude is blocked" in proc.stderr


@pytest.mark.parametrize("mode", ["pm-to-tl", "tl-to-pm", "be-implementation"])
def test_helix_handover_dump_mode_field(tmp_path: Path, capsys: pytest.CaptureFixture[str], mode: str) -> None:
    project = _init_project(tmp_path / mode)
    handover_dir = project / ".helix" / "handover"

    args = [
        "--handover-dir",
        str(handover_dir),
        "--project-root",
        str(project),
        "dump",
        "--mode",
        mode,
        "--phase",
        "L4",
        "--sprint",
        ".2",
        "--project",
        "pmo-test",
        "--files",
        "cli/helix-claude",
    ]
    if mode == "be-implementation":
        args.extend(["--task-id", "TASK-001", "--task-title", "BE implementation"])

    handover.main(args)
    capsys.readouterr()

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(project),
            "status",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    current = json.loads((handover_dir / "CURRENT.json").read_text(encoding="utf-8"))
    assert payload["mode"] == mode
    assert current["mode"] == mode
