import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_frontmatter
import yaml_parser


def _write_plan_pair(tmp_path: Path, *, plan_id: str = "PLAN-101", source_file: str | None = None) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    plan_dir = project_root / ".helix" / "plans"
    docs_dir = project_root / "docs" / "plans"
    plan_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)

    docs_path = docs_dir / f"{plan_id}-sample.md"
    docs_path.write_text(
        f"""---
plan_id: {plan_id}
title: Sample Plan
status: draft
created: 2026-05-01
finalized: null
---

## Body

content
""",
        encoding="utf-8",
    )

    source_line = "null" if source_file is None else f'"{source_file}"'
    plan_path = plan_dir / f"{plan_id}.yaml"
    plan_path.write_text(
        f"""id: {plan_id}
title: "Sample Plan"
status: draft
created_at: "2026-05-01T00:00:00Z"
source_file: {source_line}
references: []
artifacts: []
finalized_at: null
review:
  status: approve
  reviewed_at: "2026-05-01T00:00:00Z"
  review_file: ".helix/reviews/plans/{plan_id}.json"
""",
        encoding="utf-8",
    )
    return plan_path, docs_path


def test_finalize_plan_files_updates_docs_and_yaml(tmp_path: Path) -> None:
    plan_path, docs_path = _write_plan_pair(
        tmp_path, source_file="docs/plans/PLAN-101-sample.md"
    )

    resolved = plan_frontmatter.finalize_plan_files(plan_path, "2026-05-10")

    assert resolved == docs_path
    plan_data = yaml_parser.parse_yaml(plan_path.read_text(encoding="utf-8"))
    assert plan_data["status"] == "finalized"
    assert plan_data["finalized_at"] == "2026-05-10"

    frontmatter, body = plan_frontmatter._parse_frontmatter(docs_path.read_text(encoding="utf-8"))
    assert frontmatter["status"] == "finalized"
    assert frontmatter["finalized"] == "2026-05-10"
    assert "## Body" in body


def test_finalize_plan_files_falls_back_to_plan_id_glob(tmp_path: Path) -> None:
    plan_path, docs_path = _write_plan_pair(tmp_path, source_file=None)

    resolved = plan_frontmatter.finalize_plan_files(plan_path, "2026-05-10")

    assert resolved == docs_path
    frontmatter, _ = plan_frontmatter._parse_frontmatter(docs_path.read_text(encoding="utf-8"))
    assert frontmatter["finalized"] == "2026-05-10"


def test_finalize_plan_files_rolls_back_when_plan_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path, docs_path = _write_plan_pair(
        tmp_path, source_file="docs/plans/PLAN-101-sample.md"
    )
    original_plan = plan_path.read_text(encoding="utf-8")
    original_docs = docs_path.read_text(encoding="utf-8")
    monkeypatch.setenv(plan_frontmatter.FAIL_STAGE_ENV, "plan_replace")

    with pytest.raises(plan_frontmatter.PlanFrontmatterError):
        plan_frontmatter.finalize_plan_files(plan_path, "2026-05-10")

    assert plan_path.read_text(encoding="utf-8") == original_plan
    assert docs_path.read_text(encoding="utf-8") == original_docs
    assert not list(plan_path.parent.glob("*.bak.*"))
    assert not list(plan_path.parent.glob("*.tmp.*"))
    assert not list(docs_path.parent.glob("*.bak.*"))
    assert not list(docs_path.parent.glob("*.tmp.*"))


def test_finalize_plan_files_rolls_back_when_docs_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path, docs_path = _write_plan_pair(
        tmp_path, source_file="docs/plans/PLAN-101-sample.md"
    )
    original_plan = plan_path.read_text(encoding="utf-8")
    original_docs = docs_path.read_text(encoding="utf-8")
    monkeypatch.setenv(plan_frontmatter.FAIL_STAGE_ENV, "docs_replace")

    with pytest.raises(plan_frontmatter.PlanFrontmatterError):
        plan_frontmatter.finalize_plan_files(plan_path, "2026-05-10")

    assert plan_path.read_text(encoding="utf-8") == original_plan
    assert docs_path.read_text(encoding="utf-8") == original_docs
