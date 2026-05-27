from __future__ import annotations

import sys
from pathlib import Path

import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_lint
import plan_validator


def _valid_frontmatter() -> dict[str, object]:
    return {
        "plan_id": "L7-plan-lint-frontmatter-validationplan",
        "title": "Plan Lint Frontmatter Validation",
        "kind": "impl",
        "layer": "L7",
        "drive": "be",
        "status": "draft",
        "process_layer": "L7",
        "parent_design": "HELIX-workflows/helix-process/HELIX-process-L0-L14.md",
        "dependencies": {"requires": [], "blocks": []},
        "generates": [
            {
                "artifact_path": "cli/lib/plan_lint.py",
                "artifact_type": "python_module",
            }
        ],
    }


def test_validate_plan_frontmatter_missing_required() -> None:
    frontmatter = _valid_frontmatter()
    del frontmatter["kind"]

    findings = plan_lint.validate_plan_frontmatter(frontmatter)

    assert any(
        finding["level"] == "error"
        and finding["field"] == "kind"
        and "missing field: kind" in finding["message"]
        for finding in findings
    ), findings


def test_validate_plan_frontmatter_invalid_enum() -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["kind"] = "nonexistent-kind"

    findings = plan_lint.validate_plan_frontmatter(frontmatter)

    assert any(
        finding["level"] == "error"
        and finding["field"] == "kind"
        and "invalid kind" in finding["message"]
        for finding in findings
    ), findings


def test_validate_plan_frontmatter_valid() -> None:
    assert plan_lint.validate_plan_frontmatter(_valid_frontmatter()) == []


def test_validate_plan_frontmatter_accepts_v2_kinds() -> None:
    for kind in ("requirements", "planning", "basic-design", "test"):
        frontmatter = _valid_frontmatter()
        frontmatter["kind"] = kind
        assert plan_lint.validate_plan_frontmatter(frontmatter) == []


def test_frontmatter_kind_values_match_plan_validator() -> None:
    assert plan_lint.FRONTMATTER_KIND_VALUES == plan_validator.VALID_KINDS


def test_v2_plan_templates_kinds_are_covered() -> None:
    template_dir = LIB_DIR.parent / "templates" / "plan" / "v2"
    template_kinds: set[str] = set()

    for template_path in template_dir.glob("*.md"):
        text = template_path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        _, frontmatter_text, _ = text.split("---", 2)
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        kind = frontmatter.get("kind")
        if isinstance(kind, str) and kind.strip():
            template_kinds.add(kind)

    assert template_kinds
    assert template_kinds <= plan_lint.FRONTMATTER_KIND_VALUES
