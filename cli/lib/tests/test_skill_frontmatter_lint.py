from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_frontmatter_lint


def _valid_frontmatter() -> dict[str, object]:
    return {
        "name": "testing",
        "description": "This description is intentionally long enough to exceed fifty characters.",
        "triggers": ["テスト作成時"],
        "skill_id": "common/testing",
        "metadata": {"helix_layer": "L7"},
    }


def test_validate_skill_frontmatter_missing_required() -> None:
    frontmatter = _valid_frontmatter()
    del frontmatter["triggers"]

    findings = skill_frontmatter_lint.validate_skill_frontmatter(frontmatter)

    assert any(
        finding["level"] == "error"
        and finding["field"] == "triggers"
        and "missing field: triggers" in finding["message"]
        for finding in findings
    ), findings


def test_validate_skill_frontmatter_short_description() -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["description"] = "too short"

    findings = skill_frontmatter_lint.validate_skill_frontmatter(frontmatter)

    assert any(
        finding["level"] == "warning"
        and finding["field"] == "description"
        and "description too short" in finding["message"]
        for finding in findings
    ), findings


def test_scan_skills_directory_aggregates_results(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    valid_dir = skills_root / "common" / "valid-skill"
    invalid_dir = skills_root / "common" / "invalid-skill"
    valid_dir.mkdir(parents=True)
    invalid_dir.mkdir(parents=True)

    (valid_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: valid-skill",
                "description: This description is intentionally long enough to exceed fifty characters.",
                "triggers:",
                "  - trigger-a",
                "skill_id: common/valid-skill",
                "metadata:",
                "  helix_layer: L2",
                "---",
                "",
                "# body",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (invalid_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: invalid-skill",
                "description: This description is intentionally long enough to exceed fifty characters.",
                "metadata:",
                "  helix_layer: L2",
                "---",
                "",
                "# body",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = skill_frontmatter_lint.scan_skills_directory(skills_root)

    assert result["total"] == 2
    assert result["valid"] == 1
    assert result["invalid"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["file"].endswith("common/invalid-skill/SKILL.md")
    assert any(
        finding["field"] == "triggers" and "missing field: triggers" in finding["message"]
        for finding in result["errors"][0]["errors"]
    )
