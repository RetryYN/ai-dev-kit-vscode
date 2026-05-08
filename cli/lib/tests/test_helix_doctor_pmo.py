from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .test_role_config_consistency import REPO_ROOT, _copy_roles_and_config, _run_helix_doctor


def _set_role_metadata_value(config_path: Path, key_path: str, value: str) -> None:
    subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "cli/lib/yaml_parser.py"),
            "write",
            str(config_path),
            key_path,
            value,
        ],
        check=True,
    )


def test_pmo_sonnet_consistency_pass() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        home_root = working_dir / "home"
        home_root.mkdir()

        _copy_roles_and_config(working_dir)

        result = _run_helix_doctor(working_dir, home_root)

        assert result.returncode == 0
        assert "  ✓ pmo role consistency" in result.stdout
        assert "WARNING: pmo role pmo-sonnet" not in result.stdout


def test_pmo_sonnet_mismatched_thinking_is_warn() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        home_root = working_dir / "home"
        home_root.mkdir()

        _copy_roles_and_config(working_dir)
        _set_role_metadata_value(working_dir / "cli/config/models.yaml", "role_metadata.pmo-sonnet.thinking", "high")

        result = _run_helix_doctor(working_dir, home_root)

        assert result.returncode == 0
        assert "WARNING: pmo role pmo-sonnet: claude_thinking" in result.stdout
        assert "  △ pmo role consistency" in result.stdout


def test_pmo_haiku_consistency_pass() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        home_root = working_dir / "home"
        home_root.mkdir()

        _copy_roles_and_config(working_dir)

        result = _run_helix_doctor(working_dir, home_root)

        assert result.returncode == 0
        assert "  ✓ pmo role consistency" in result.stdout
        assert "WARNING: pmo role pmo-haiku" not in result.stdout


def test_pmo_haiku_mismatched_allow_paths_is_warn() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        home_root = working_dir / "home"
        home_root.mkdir()

        _copy_roles_and_config(working_dir)
        _set_role_metadata_value(working_dir / "cli/config/models.yaml", "role_metadata.pmo-haiku.allow_paths", "docs/**")

        result = _run_helix_doctor(working_dir, home_root)

        assert result.returncode == 0
        assert "WARNING: pmo role pmo-haiku: claude_allow_paths" in result.stdout
        assert "  △ pmo role consistency" in result.stdout
