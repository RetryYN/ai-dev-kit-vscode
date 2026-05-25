from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_health


def _write_plan(path: Path, frontmatter: str, body: str = "## body\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")


def test_scan_all_plans_counts_distribution(tmp_path: Path) -> None:
    plans_root = tmp_path / "docs" / "plans"
    _write_plan(
        plans_root / "L7" / "L7-alpha-plan.md",
        "\n".join(
            [
                "plan_id: L7-alpha-plan",
                "title: Alpha",
                "kind: impl",
                "layer: L7",
                "drive: be",
                "status: draft",
                "process_layer: L7",
                "parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md",
            ]
        ),
    )
    _write_plan(
        plans_root / "L5" / "L5-beta-plan.md",
        "\n".join(
            [
                "plan_id: L5-beta-plan",
                "title: Beta",
                "kind: design",
                "layer: L5",
                "drive: be",
                "status: completed",
                "process_layer: L5",
            ]
        ),
    )
    _write_plan(
        plans_root / "misc" / "other-plan.md",
        "\n".join(
            [
                "plan_id: L3-gamma-plan",
                "title: Gamma",
                "kind: poc",
                "layer: L3",
                "drive: be",
                "status: archived",
                "process_layer: L3",
            ]
        ),
    )

    result = plan_health.scan_all_plans(plans_root)

    assert result["total"] == 3
    assert result["valid_frontmatter"] == 2
    assert result["invalid_frontmatter"] == 1
    assert result["status_distribution"] == {
        "draft": 1,
        "in_progress": 0,
        "completed": 1,
        "finalized": 0,
        "other": 1,
    }
    assert result["kind_distribution"] == {
        "design": 1,
        "impl": 1,
        "poc": 1,
    }
    assert len(result["invalid_examples"]) == 1
    assert result["invalid_examples"][0]["file"].endswith("other-plan.md")
    assert any("invalid status: archived" in error for error in result["invalid_examples"][0]["errors"])


def test_scan_all_plans_detects_invalid(tmp_path: Path) -> None:
    plans_root = tmp_path / "docs" / "plans"
    _write_plan(
        plans_root / "L7" / "L7-valid-plan.md",
        "\n".join(
            [
                "plan_id: L7-valid-plan",
                "title: Valid",
                "kind: impl",
                "layer: L7",
                "drive: be",
                "status: in_progress",
                "process_layer: L7",
                "parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md",
            ]
        ),
    )
    _write_plan(
        plans_root / "L7" / "L7-invalid-plan.md",
        "\n".join(
            [
                "plan_id: L7-invalid-plan",
                "title: Invalid",
                "layer: L7",
                "drive: be",
                "status: draft",
            ]
        ),
    )

    result = plan_health.scan_all_plans(plans_root)

    assert result["total"] == 2
    assert result["valid_frontmatter"] == 1
    assert result["invalid_frontmatter"] == 1
    assert result["status_distribution"] == {
        "draft": 1,
        "in_progress": 1,
        "completed": 0,
        "finalized": 0,
        "other": 0,
    }
    assert result["kind_distribution"] == {"impl": 1}
    assert len(result["invalid_examples"]) == 1
    assert result["invalid_examples"][0]["file"].endswith("L7-invalid-plan.md")
    assert any("missing field: kind" in error for error in result["invalid_examples"][0]["errors"])


def test_scan_all_plans_handles_empty_dir(tmp_path: Path) -> None:
    result = plan_health.scan_all_plans(tmp_path / "empty")

    assert result == {
        "total": 0,
        "valid_frontmatter": 0,
        "invalid_frontmatter": 0,
        "status_distribution": {
            "draft": 0,
            "in_progress": 0,
            "completed": 0,
            "finalized": 0,
            "other": 0,
        },
        "kind_distribution": {},
        "invalid_examples": [],
    }
