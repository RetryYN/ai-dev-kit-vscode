from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_deps_helper


def _write_plan(
    docs_dir: Path,
    *,
    plan_id: str,
    dependencies: str = "",
    generates: str = "",
) -> Path:
    path = docs_dir / f"{plan_id}-sample.md"
    body = [
        "---",
        f"plan_id: {plan_id}",
        "title: Sample Plan",
        "kind: impl",
        "layer: L4",
        "drive: be",
        "status: draft",
    ]
    if dependencies:
        body.extend(dependencies.strip("\n").splitlines())
    if generates:
        body.extend(generates.strip("\n").splitlines())
    body.extend(["---", "", "# Body", ""])
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def _prepare_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "docs" / "plans").mkdir(parents=True)
    return project


def test_dependency_payload_reads_parent_requires_and_blocks(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    docs_dir = project / "docs" / "plans"
    _write_plan(
        docs_dir,
        plan_id="PLAN-091",
        dependencies="""
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-087
    - PLAN-088
  blocks:
    - PLAN-092
""",
    )

    payload = plan_deps_helper.dependency_payload("PLAN-091", project)

    assert payload["doc_path"] == "docs/plans/PLAN-091-sample.md"
    assert payload["dependencies"]["parent"] == "PLAN-MM-001"
    assert payload["dependencies"]["requires"] == ["PLAN-087", "PLAN-088"]
    assert payload["dependencies"]["blocks"] == ["PLAN-092"]


def test_render_dependency_tree_expands_nested_requires_with_depth(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    docs_dir = project / "docs" / "plans"
    _write_plan(
        docs_dir,
        plan_id="PLAN-091",
        dependencies="""
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-092
  blocks: []
""",
    )
    _write_plan(
        docs_dir,
        plan_id="PLAN-092",
        dependencies="""
dependencies:
  parent: null
  requires:
    - PLAN-093
  blocks: []
""",
    )
    _write_plan(
        docs_dir,
        plan_id="PLAN-093",
        dependencies="""
dependencies:
  parent: null
  requires: []
  blocks: []
""",
    )

    rendered = plan_deps_helper.render_dependency_tree("PLAN-091", depth=2, project_root=project)

    assert "PLAN-091" in rendered
    assert "parent" in rendered
    assert "PLAN-092" in rendered
    assert "PLAN-093" in rendered


def test_generates_payload_lists_artifacts(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    docs_dir = project / "docs" / "plans"
    _write_plan(
        docs_dir,
        plan_id="PLAN-091",
        generates="""
generates:
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/lib/plan_validator.py
    artifact_type: python_module
""",
    )

    payload = plan_deps_helper.generates_payload("PLAN-091", project)

    assert payload["artifacts"] == [
        {"artifact_path": "cli/helix-plan", "artifact_type": "cli_extension"},
        {"artifact_path": "cli/lib/plan_validator.py", "artifact_type": "python_module"},
    ]


def test_reverse_generates_lookup_returns_matching_plan(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    docs_dir = project / "docs" / "plans"
    _write_plan(
        docs_dir,
        plan_id="PLAN-091",
        generates="""
generates:
  - artifact_path: cli/lib/plan_validator.py
    artifact_type: python_module
""",
    )
    _write_plan(
        docs_dir,
        plan_id="PLAN-092",
        generates="""
generates:
  - artifact_path: cli/lib/other.py
    artifact_type: python_module
""",
    )

    matches = plan_deps_helper.reverse_generates_lookup("cli/lib/plan_validator.py", project)

    assert matches == [
        {
            "plan_id": "PLAN-091",
            "doc_path": "docs/plans/PLAN-091-sample.md",
            "artifact_path": "cli/lib/plan_validator.py",
            "artifact_type": "python_module",
        }
    ]


def test_frontmatter_text_preserves_yaml_keys(tmp_path: Path) -> None:
    project = _prepare_project(tmp_path)
    docs_dir = project / "docs" / "plans"
    _write_plan(
        docs_dir,
        plan_id="PLAN-091",
        dependencies="""
dependencies:
  parent: PLAN-MM-001
  requires: []
  blocks: []
""",
        generates="""
generates:
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
""",
    )

    rendered = plan_deps_helper.frontmatter_text("PLAN-091", project)

    assert "plan_id: PLAN-091" in rendered
    assert "dependencies:" in rendered
    assert "generates:" in rendered
