from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_helix_layer_audit


def test_audit_skill_helix_layers_counts_distribution(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    foo_dir = skills_root / "foo"
    bar_dir = skills_root / "bar"
    foo_dir.mkdir(parents=True)
    bar_dir.mkdir(parents=True)

    (foo_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: foo",
                "description: This description is intentionally long enough to exceed fifty characters.",
                "triggers:",
                "  - trigger-a",
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
    (bar_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: bar",
                "description: This description is intentionally long enough to exceed fifty characters.",
                "triggers:",
                "  - trigger-b",
                "---",
                "",
                "# body",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = skill_helix_layer_audit.audit_skill_helix_layers(skills_root)

    assert result["total_skills"] == 2
    assert result["with_helix_layer"] == 1
    assert result["without_helix_layer"] == 1
    assert result["invalid_helix_layer"] == 0
    assert result["distribution"]["L2"] == 1
    assert result["distribution"]["missing"] == 1


def test_audit_skill_helix_layers_detects_invalid(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    baz_dir = skills_root / "baz"
    baz_dir.mkdir(parents=True)

    (baz_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: baz",
                "description: This description is intentionally long enough to exceed fifty characters.",
                "triggers:",
                "  - trigger-c",
                "metadata:",
                "  helix_layer: L99",
                "---",
                "",
                "# body",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = skill_helix_layer_audit.audit_skill_helix_layers(skills_root)

    assert result["total_skills"] == 1
    assert result["with_helix_layer"] == 1
    assert result["without_helix_layer"] == 0
    assert result["invalid_helix_layer"] == 1
    assert result["distribution"]["missing"] == 0
    assert result["invalid_examples"] == [
        {
            "file": "baz/SKILL.md",
            "helix_layer_value": "L99",
            "reason": "invalid helix_layer: expected one of L1-L14 or all",
        }
    ]


def test_audit_skill_helix_layers_handles_empty_directory(tmp_path: Path) -> None:
    result = skill_helix_layer_audit.audit_skill_helix_layers(tmp_path / "missing-skills")

    assert result["total_skills"] == 0
    assert result["with_helix_layer"] == 0
    assert result["without_helix_layer"] == 0
    assert result["invalid_helix_layer"] == 0
    assert all(count == 0 for count in result["distribution"].values())
    assert result["invalid_examples"] == []
