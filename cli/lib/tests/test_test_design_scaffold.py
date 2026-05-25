"""Tests for cli.lib.test_design_scaffold."""

from __future__ import annotations

from cli.lib.test_design_scaffold import (
    auto_detect_paired_design,
    extract_function_signatures,
    extract_paired_design_sections,
    generate_skeleton,
    write_scaffold,
)


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


def test_extract_paired_design_sections_finds_acceptance(tmp_path) -> None:
    """DoD 検証: W13 U-001 paired design doc から受入条件 section を抽出する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

## §1 受入条件

- acceptance text

## §3 補足

- note
""",
        encoding="utf-8",
    )

    sections = extract_paired_design_sections(paired_design)

    assert "acceptance text" in sections["acceptance"]
    assert sections["function_spec"] == ""


def test_generate_skeleton_with_extract_sections_includes_acceptance(tmp_path) -> None:
    """DoD 検証: W13 U-002 extract_sections=True で受入条件引用を注入する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

## §1 受入条件

- acceptance text
""",
        encoding="utf-8",
    )

    skeleton = generate_skeleton("L4", str(paired_design), extract_sections=True)

    assert "> - acceptance text" in skeleton


def test_generate_skeleton_extract_sections_handles_missing_file() -> None:
    """DoD 検証: W13 U-003 missing file でも extract_sections=True で落ちない。"""
    skeleton = generate_skeleton(
        "L4",
        "docs/plans/L4/not-found.md",
        extract_sections=True,
    )

    assert "## §1 受入条件" in skeleton
    assert "TODO: pair design doc から DoD を引き写す" in skeleton


def test_auto_detect_paired_design_finds_first_match(tmp_path) -> None:
    """DoD 検証: W16 U-001 pair layer 配下の最初の PLAN を auto detect する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-foo-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    (pair_dir / "L9-bar-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path)

    assert detected == "docs/plans/L9/L9-bar-plan.md"


def test_auto_detect_paired_design_returns_none_when_no_pair(tmp_path) -> None:
    """DoD 検証: W16 U-002 pair なし layer は None を返す。"""
    assert auto_detect_paired_design("L0", project_root=tmp_path) is None


def test_auto_detect_paired_design_returns_none_when_no_match(tmp_path) -> None:
    """DoD 検証: W16 U-003 pair layer に match が無いとき None を返す。"""
    assert auto_detect_paired_design("L4", project_root=tmp_path) is None


def test_auto_detect_paired_design_prefers_draft_status(tmp_path) -> None:
    """DoD 検証: W20 U-001 prefer_status='draft' なら draft 候補を優先する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-completed-plan.md").write_text("---\nstatus: completed\n---\n", encoding="utf-8")
    (pair_dir / "L9-z-draft-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_status="draft")

    assert detected == "docs/plans/L9/L9-z-draft-plan.md"


def test_auto_detect_paired_design_fallback_to_first_when_no_preferred(tmp_path) -> None:
    """DoD 検証: W20 U-002 prefer_status 未該当時は sorted 最初へ fallback する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-completed-plan.md").write_text("---\nstatus: completed\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_status="draft")

    assert detected == "docs/plans/L9/L9-a-completed-plan.md"


def test_auto_detect_paired_design_none_disables_preference(tmp_path) -> None:
    """DoD 検証: W20 U-003 prefer_status=None なら従来の sorted 最初を使う。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-completed-plan.md").write_text("---\nstatus: completed\n---\n", encoding="utf-8")
    (pair_dir / "L9-z-draft-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_status=None)

    assert detected == "docs/plans/L9/L9-a-completed-plan.md"


def test_auto_detect_paired_design_prefers_design_kind(tmp_path) -> None:
    """DoD 検証: W22 U-001 prefer_kind='design' なら design 候補を優先する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-poc-plan.md").write_text("---\nkind: poc\nstatus: draft\n---\n", encoding="utf-8")
    (pair_dir / "L9-design-plan.md").write_text("---\nkind: design\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_kind="design")

    assert detected == "docs/plans/L9/L9-design-plan.md"


def test_auto_detect_paired_design_fallback_when_no_preferred_kind(tmp_path) -> None:
    """DoD 検証: W22 U-002 prefer_kind 未該当時は sorted 最初へ fallback する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-impl-plan.md").write_text("---\nkind: impl\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_kind="design")

    assert detected == "docs/plans/L9/L9-impl-plan.md"


def test_auto_detect_paired_design_prefer_status_and_kind_combined(tmp_path) -> None:
    """DoD 検証: W22 U-003 prefer_status と prefer_kind 両一致を最優先する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-old-design-completed-plan.md").write_text(
        "---\nkind: design\nstatus: completed\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-new-design-draft-plan.md").write_text(
        "---\nkind: design\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-impl-draft-plan.md").write_text("---\nkind: impl\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design(
        "L4",
        project_root=tmp_path,
        prefer_status="draft",
        prefer_kind="design",
    )

    assert detected == "docs/plans/L9/L9-new-design-draft-plan.md"


def test_extract_function_signatures_finds_python_def(tmp_path) -> None:
    """DoD 検証: W21 U-001 paired design doc から Python def を抽出する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

def my_function(arg1, arg2):
    return arg1 + arg2
""",
        encoding="utf-8",
    )

    signatures = extract_function_signatures(paired_design)

    assert signatures[0]["name"] == "my_function"
    assert "def my_function(arg1, arg2):" in signatures[0]["signature"]
    assert "return arg1 + arg2" in signatures[0]["context"]


def test_extract_function_signatures_truncates_at_max_count(tmp_path) -> None:
    """DoD 検証: W21 U-002 max_count を超える関数定義は truncate する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        "\n".join(f"def func_{chr(97 + index)}():" for index in range(10)),
        encoding="utf-8",
    )

    signatures = extract_function_signatures(paired_design, max_count=3)

    assert len(signatures) == 3


def test_generate_skeleton_with_extract_functions_includes_tc_per_function(tmp_path) -> None:
    """DoD 検証: W21 U-003 extract_functions=True で関数別 TC を展開する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

def first_case():
    return 1

def second_case():
    return 2
""",
        encoding="utf-8",
    )

    skeleton = generate_skeleton("L4", str(paired_design), extract_functions=True)

    assert "### TC-001: `first_case`" in skeleton
    assert "### TC-002: `second_case`" in skeleton
    assert "> signature: `def first_case():`" in skeleton
