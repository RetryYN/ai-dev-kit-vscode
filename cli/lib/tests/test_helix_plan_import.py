from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import yaml_parser


CLI = REPO_ROOT / "cli" / "helix-plan"


def _prepare_project(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    project = tmp_path / "project"
    (project / ".helix" / "plans").mkdir(parents=True)
    (project / "docs" / "plans").mkdir(parents=True)
    home = tmp_path / "home"
    home.mkdir()

    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    env["HOME"] = str(home)
    return project, env


def _run_plan(project: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_plan_markdown(
    project: Path,
    *,
    plan_id: str = "PLAN-101",
    status: str = "completed",
    with_frontmatter: bool = True,
) -> Path:
    docs_path = project / "docs" / "plans" / f"{plan_id}-sample.md"
    if with_frontmatter:
        docs_path.write_text(
            f"""---
plan_id: {plan_id}
title: Imported Plan
status: {status}
created: 2026-05-01
finalized: 2026-05-03
---

# Body
""",
            encoding="utf-8",
        )
    else:
        docs_path.write_text("# Body\n", encoding="utf-8")
    return docs_path


def _read_plan_yaml(project: Path, plan_id: str = "PLAN-101") -> dict:
    plan_path = project / ".helix" / "plans" / f"{plan_id}.yaml"
    return yaml_parser.parse_yaml(plan_path.read_text(encoding="utf-8"))


def test_import_creates_yaml_from_frontmatter(tmp_path: Path) -> None:
    project, env = _prepare_project(tmp_path)
    _write_plan_markdown(project)

    result = _run_plan(project, env, "import", "--from-frontmatter")

    assert result.returncode == 0, result.stderr
    plan = _read_plan_yaml(project)
    assert plan["id"] == "PLAN-101"
    assert plan["status"] == "finalized"
    assert plan["source_file"] == "docs/plans/PLAN-101-sample.md"
    assert plan["review"]["status"] == "approve"
    assert plan["review"]["reviewed_at"] == "2026-05-01T00:00:00Z"


def test_import_skips_existing_yaml_without_force(tmp_path: Path) -> None:
    project, env = _prepare_project(tmp_path)
    _write_plan_markdown(project)
    plan_path = project / ".helix" / "plans" / "PLAN-101.yaml"
    plan_path.write_text("id: PLAN-101\ntitle: Existing\nstatus: draft\n", encoding="utf-8")

    result = _run_plan(project, env, "import", "--from-frontmatter")

    assert result.returncode == 0, result.stderr
    assert "skip exists .helix/plans/PLAN-101.yaml" in result.stdout
    assert "title: Existing" in plan_path.read_text(encoding="utf-8")


def test_import_overwrites_with_force(tmp_path: Path) -> None:
    project, env = _prepare_project(tmp_path)
    _write_plan_markdown(project)
    plan_path = project / ".helix" / "plans" / "PLAN-101.yaml"
    plan_path.write_text("id: PLAN-101\ntitle: Existing\nstatus: draft\n", encoding="utf-8")

    result = _run_plan(project, env, "import", "--from-frontmatter", "--force")

    assert result.returncode == 0, result.stderr
    plan = _read_plan_yaml(project)
    assert "overwrite .helix/plans/PLAN-101.yaml" in result.stdout
    assert plan["title"] == "Imported Plan"
    assert plan["finalized_at"] == "2026-05-03T00:00:00Z"


def test_import_skips_no_frontmatter_md(tmp_path: Path) -> None:
    project, env = _prepare_project(tmp_path)
    _write_plan_markdown(project, with_frontmatter=False)

    result = _run_plan(project, env, "import", "--from-frontmatter")

    assert result.returncode == 0, result.stderr
    assert "skip no-frontmatter docs/plans/PLAN-101-sample.md" in result.stdout
    assert not (project / ".helix" / "plans" / "PLAN-101.yaml").exists()


def test_import_dry_run_no_write(tmp_path: Path) -> None:
    project, env = _prepare_project(tmp_path)
    _write_plan_markdown(project)

    result = _run_plan(project, env, "import", "--from-frontmatter", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "dry-run create .helix/plans/PLAN-101.yaml" in result.stdout
    assert not (project / ".helix" / "plans" / "PLAN-101.yaml").exists()
