from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_lint


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
    frontmatter["kind"] = "invalid"

    findings = plan_lint.validate_plan_frontmatter(frontmatter)

    assert any(
        finding["level"] == "error"
        and finding["field"] == "kind"
        and "invalid kind" in finding["message"]
        for finding in findings
    ), findings


def test_validate_plan_frontmatter_valid() -> None:
    assert plan_lint.validate_plan_frontmatter(_valid_frontmatter()) == []
