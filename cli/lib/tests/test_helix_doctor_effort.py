"""PLAN-046 W-1: helix-doctor の role effort 整合性 check のテスト"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCTOR = REPO_ROOT / "cli" / "helix-doctor"


def _prepare_project_root(project_root: Path) -> None:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "cli/templates/phase.yaml", helix_dir / "phase.yaml")
    shutil.copy2(REPO_ROOT / "cli/templates/gate-checks.yaml", helix_dir / "gate-checks.yaml")
    shutil.copy2(REPO_ROOT / "cli/templates/doc-map.yaml", helix_dir / "doc-map.yaml")
    (helix_dir / "matrix.yaml").write_text("deliverables: []\n", encoding="utf-8")
    (project_root / "home").mkdir(exist_ok=True)


def _run_doctor(
    project_root: Path,
    doctor_path: Path = DOCTOR,
    helix_home: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HELIX_HOME": str(helix_home),
        "HELIX_PROJECT_ROOT": str(project_root),
        "HOME": str(project_root / "home"),
    }
    return subprocess.run(
        [str(doctor_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        check=False,
    )


def test_normal_no_effort_drift(tmp_path: Path) -> None:
    """全 role conf が文書と整合 → role effort 整合性 ✓ 表示"""
    _prepare_project_root(tmp_path)

    result = _run_doctor(tmp_path)
    output = result.stdout + result.stderr

    assert result.returncode in (0, 1)
    assert "role effort" in output.lower()
    assert "✓ role effort 整合性" in output


def test_anomaly_detected_with_fixture(tmp_path: Path) -> None:
    """fixture で role conf を意図的に不整合にして warn 検出"""
    repo_copy = tmp_path / "repo"
    shutil.copytree(
        REPO_ROOT,
        repo_copy,
        dirs_exist_ok=False,
        ignore=shutil.ignore_patterns(".git", ".helix", "__pycache__"),
    )
    _prepare_project_root(repo_copy)

    pg_conf = repo_copy / "cli" / "roles" / "pg.conf"
    pg_conf.write_text(
        pg_conf.read_text(encoding="utf-8").replace("codex_thinking=medium", "codex_thinking=high"),
        encoding="utf-8",
    )

    result = _run_doctor(repo_copy, repo_copy / "cli" / "helix-doctor", repo_copy)
    output = result.stdout + result.stderr

    assert "role effort" in output.lower()
    assert "drift" in output.lower() or "△" in output
