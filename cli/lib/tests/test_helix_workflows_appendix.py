from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_helix_workflows_appendix.py"
SPEC = importlib.util.spec_from_file_location("helix_workflows_appendix", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_workflow_entries_cover_expected_files() -> None:
    names = [entry["file"] for entry in MODULE.WORKFLOW_ENTRIES]

    assert len(names) == 45
    assert len(set(names)) == 45
    assert "README.md" not in names
    assert names[0] == "L0-concept.md"
    assert names[-1] == "two-stage-agent-design.md"


def test_apply_integration_target_adds_value_idempotently(tmp_path: Path) -> None:
    target = tmp_path / "sample.md"
    target.write_text(
        """---
doc_id: sample
title: Sample
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Body
""",
        encoding="utf-8",
    )

    first = MODULE.apply_integration_target(
        target,
        "docs/design",
        "L0-L14 工程",
        write=True,
    )
    second = MODULE.apply_integration_target(
        target,
        "docs/design",
        "L0-L14 工程",
        write=True,
    )

    assert first == "updated"
    assert second == "skipped"

    frontmatter, _body = MODULE._split_frontmatter(target.read_text(encoding="utf-8"))
    assert list(frontmatter.keys()) == [
        "doc_id",
        "title",
        "status",
        "created",
        "owner",
        "parent",
        "integration_target",
    ]
    assert frontmatter["integration_target"] == {
        "docs_path": "docs/design",
        "category": "L0-L14 工程",
    }


def test_apply_integration_target_rejects_conflict(tmp_path: Path) -> None:
    target = tmp_path / "sample.md"
    target.write_text(
        """---
doc_id: sample
title: Sample
status: draft
integration_target:
  docs_path: docs/requirements
  category: L0-L14 工程
---

# Body
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="conflicting integration_target"):
        MODULE.apply_integration_target(target, "docs/design", "L0-L14 工程", write=True)


def test_render_appendix_documents_include_required_sections() -> None:
    documents = MODULE.render_appendix_documents()

    architecture = documents[MODULE.ARCHITECTURE_APPENDIX]
    design = documents[MODULE.DESIGN_APPENDIX]
    research = documents[MODULE.RESEARCH_APPENDIX]

    assert "## 中央 INDEX" in architecture
    assert "| file | primary_category | docs_path | appendix_file | link |" in architecture
    assert architecture.count("| L") >= 15
    assert "README.md は navigation 文書" in architecture
    assert "Recovery/Incident 運用" in architecture

    assert "## 概要" in design
    assert "## 対象 file list" in design
    assert "## 参照方針" in design
    assert "incident-workflow.md" in design
    assert "frontend-design-workflow.md" in design

    assert "cross-cutting-mechanisms.md" in research
    assert "実体ファイルは移動せず" in research


def test_rendered_frontmatter_is_yaml_mapping() -> None:
    target = REPO_ROOT / "HELIX-workflows" / "helix-process" / "L0-concept.md"
    frontmatter, _body = MODULE._split_frontmatter(target.read_text(encoding="utf-8"))
    rendered = MODULE._render_frontmatter(frontmatter, "# Body\n")
    parsed, _ = MODULE._split_frontmatter(rendered)

    assert isinstance(yaml.safe_load(yaml.safe_dump(parsed, sort_keys=False)), dict)
