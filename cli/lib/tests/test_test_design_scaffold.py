"""Tests for cli.lib.test_design_scaffold."""

from __future__ import annotations

from cli.lib.test_design_scaffold import generate_skeleton, write_scaffold


def test_generate_skeleton_includes_layer_and_pair() -> None:
    """DoD 検証: W9-C U-001 L4 design から L9 pair skeleton を生成する。"""
    skeleton = generate_skeleton(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        title="Sample Design",
    )

    assert "target_layer: 'L9'" in skeleton
    assert "paired_design_layer: 'L4'" in skeleton
    assert "TEST-DESIGN-L9" in skeleton
    assert "V-model L4↔L9" in skeleton


def test_generate_skeleton_includes_template_sections() -> None:
    """DoD 検証: W9-C U-002 skeleton に §0-§3 を含む。"""
    skeleton = generate_skeleton(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        title="Sample Design",
    )

    assert "## §0 対応設計" in skeleton
    assert "## §1 受入条件" in skeleton
    assert "## §2 テストケース" in skeleton
    assert "## §3 トレース" in skeleton


def test_write_scaffold_dry_run_no_write(tmp_path) -> None:
    """DoD 検証: W9-C U-003 dry_run=True ではファイルを書かない。"""
    result = write_scaffold(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        project_root=tmp_path,
        dry_run=True,
    )

    assert result["status"] == "dry_run"
    assert result["reason"] == "dry run"
    assert not list(tmp_path.rglob("TEST-DESIGN-L9-*.md"))


def test_write_scaffold_apply_writes_file(tmp_path) -> None:
    """DoD 検証: W9-C U-004 dry_run=False では scaffold を書き込む。"""
    output_path = tmp_path / "docs" / "plans" / "L9" / "TEST-DESIGN-L9-custom.md"

    result = write_scaffold(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        project_root=tmp_path,
        dry_run=False,
        output_path=output_path,
    )

    assert result["status"] == "applied"
    assert result["output_path"] == str(output_path)
    assert output_path.exists()
    assert "paired_design_doc: 'docs/plans/L4/L4-sample-design-plan.md'" in output_path.read_text(
        encoding="utf-8"
    )


def test_write_scaffold_skips_existing(tmp_path) -> None:
    """DoD 検証: W9-C U-005 既存 path には上書きせず skip する。"""
    output_path = tmp_path / "docs" / "plans" / "L9" / "TEST-DESIGN-L9-custom.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("existing\n", encoding="utf-8")

    result = write_scaffold(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        project_root=tmp_path,
        dry_run=False,
        output_path=output_path,
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "file exists"
    assert output_path.read_text(encoding="utf-8") == "existing\n"
