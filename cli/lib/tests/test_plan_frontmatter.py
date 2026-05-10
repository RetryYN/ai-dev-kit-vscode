import hashlib
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import plan_frontmatter
import yaml_parser


def _body_hash(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text = text[end + 5 :]
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


@pytest.mark.parametrize(
    ("relative_path", "expected_hash"),
    [
        (
            "docs/plans/PLAN-001-poc-skill.md",
            "8c274a294fd011490f5b4f3d7ec1f8cce7146fa7fbda5277221a52edd4c09e6a",
        ),
        (
            "docs/plans/PLAN-002-helix-fullauto-foundation.md",
            "13112fd62ad47b6691fc01f4390876b951074671193e2e4b926998f880bbcb5b",
        ),
        (
            "docs/plans/PLAN-003-auto-restart-foundation.md",
            "4f6f5e7b1bd2530bce9a1ee5ff628a009def70e52f844cd2c5e037e29634305e",
        ),
        (
            "docs/plans/PLAN-004-pm-reward-design.md",
            "aa98e2f8b758b1befd7447145bbd934fcbe18dc5f77a74605af509d13f4c7129",
        ),
        (
            "docs/plans/PLAN-005-ops-automation-skills.md",
            "0dfd9168fa81ef11b9078bda38b8a2730b561d296c59b84de24b63eda5ca13a9",
        ),
        (
            "docs/plans/PLAN-006-upstream-meta-phase.md",
            "b16f9c3982eba63cb5cc049c408dbc75115f833ae2190ff5b29cadffbf93cd94",
        ),
        (
            "docs/plans/PLAN-007-scrum-multitype-trigger.md",
            "54dc289cd3ed1f70f06110e132ae451830e120bf1b85b06122271f510e193fca",
        ),
        (
            "docs/plans/PLAN-008-reverse-multitype.md",
            "037f226d132b311082b967248c1609e01ce1f23342a8ad60c9c87133b16f2349",
        ),
        (
            "docs/plans/PLAN-009-run-phase-l9-l11.md",
            "7b95356501deecea682826cd65d8f191c378123e9693c7ac1d1a422bec5ee63f",
        ),
        (
            "docs/plans/PLAN-010-verification-agent.md",
            "51cc01d52bee42d953364b11c1883113bbaa05efcaa655c27c4b2418afa9841f",
        ),
        (
            "docs/plans/PLAN-011-code-index-system.md",
            "1721a90d7154a3f4d235e708c116b514b40fa7a41a25ff701f6c67960260dfb0",
        ),
    ],
)
def test_legacy_plan_body_hash_is_preserved(
    relative_path: str,
    expected_hash: str,
) -> None:
    text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    assert _body_hash(text) == expected_hash
