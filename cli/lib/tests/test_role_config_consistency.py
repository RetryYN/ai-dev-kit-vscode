from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _copy_roles_and_config(working_dir: Path) -> None:
    cli_dir = working_dir / "cli"
    (cli_dir / "lib").mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_ROOT / "cli/roles", cli_dir / "roles", dirs_exist_ok=True)
    shutil.copytree(REPO_ROOT / "cli/config", cli_dir / "config", dirs_exist_ok=True)
    shutil.copy2(REPO_ROOT / "cli/lib/yaml_parser.py", cli_dir / "lib" / "yaml_parser.py")


def _sync_models_with_roles(models_path: Path) -> None:
    lines = models_path.read_text(encoding="utf-8").splitlines(keepends=True)
    role_models = {}
    roles_dir = models_path.parent.parent / "roles"
    for role_file in roles_dir.glob("*.conf"):
        role = role_file.stem
        for line in role_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("codex_model="):
                role_models[role] = line.split("=", 1)[1]
                break

    in_roles = False
    next_lines = []
    for line in lines:
        if line.startswith("roles:"):
            in_roles = True
            next_lines.append(line)
            continue

        if in_roles and not line.startswith("  "):
            in_roles = False

        if in_roles:
            matched = False
            if ":" in line:
                key = line.split(":", 1)[0].strip()
                if key in role_models:
                    next_lines.append(f"  {key}: {role_models[key]}\n")
                    matched = True
            if matched:
                continue

        next_lines.append(line)

    models_path.write_text("".join(next_lines), encoding="utf-8")


def _run_helix_doctor(helix_home: Path, home_root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(helix_home)
    env["HELIX_PROJECT_ROOT"] = str(REPO_ROOT)
    env["HOME"] = str(home_root)
    return subprocess.run(
        [str(REPO_ROOT / "cli/helix-doctor")],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_all_roles_consistent() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        home_root = working_dir / "home"
        home_root.mkdir()

        _copy_roles_and_config(working_dir)
        _sync_models_with_roles(working_dir / "cli/config/models.yaml")
        result = _run_helix_doctor(working_dir, home_root)

        assert result.returncode == 0
        assert "WARNING: role" not in result.stdout


def test_detects_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        home_root = working_dir / "home"
        home_root.mkdir()

        _copy_roles_and_config(working_dir)

        target = working_dir / "cli/config/models.yaml"
        text = target.read_text(encoding="utf-8")
        target.write_text(text.replace("  security: gpt-5.4", "  security: gpt-5.3-codex", 1), encoding="utf-8")

        result = _run_helix_doctor(working_dir, home_root)

        assert result.returncode == 0
        assert (
            "WARNING: role security: conf=gpt-5.4, yaml=gpt-5.3-codex (mismatch)"
            in result.stdout
        )
