import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import review_output


SCHEMA_PATH = REPO_ROOT / "cli" / "schemas" / "review-output.schema.json"
TEMPLATE_PATH = REPO_ROOT / "cli" / "templates" / "codex-review-prompt.md"
REVIEW_ROLES = ("tl", "se", "pg", "qa", "security", "dba", "devops", "docs")


def _schema() -> dict:
    return review_output.load_schema(SCHEMA_PATH)


def _base_review(**overrides):
    payload = {
        "verdict": "approve",
        "summary": "P0/P1/P2/P3: 0/0/0/0。approve。",
        "overall_scores": [
            {"dimension": "density", "level": 4, "comment": "網羅されている"},
            {"dimension": "depth", "level": 3, "comment": "必要十分"},
            {"dimension": "breadth", "level": 4, "comment": "関連領域を確認"},
            {"dimension": "accuracy", "level": 5, "comment": "仕様と一致"},
            {"dimension": "maintainability", "level": 4, "comment": "保守しやすい"},
        ],
        "findings": [],
        "next_steps": ["なし"],
    }
    payload.update(overrides)
    return payload


def test_prompt_template_contains_5_dimensions() -> None:
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    for dimension in review_output.DIMENSIONS:
        assert dimension in text
    assert "Lv1" in text
    assert "Lv5" in text
    assert "overall_scores" in text
    assert "dimension_scores" in text


def test_role_conf_loads_template_path() -> None:
    for role in REVIEW_ROLES:
        conf = (REPO_ROOT / "cli" / "roles" / f"{role}.conf").read_text(encoding="utf-8")
        assert "review_template_path=cli/templates/codex-review-prompt.md" in conf


def test_review_schema_validates_overall_scores() -> None:
    normalized = review_output.normalize_review(_base_review(), _schema())
    assert [score["dimension"] for score in normalized["overall_scores"]] == list(review_output.DIMENSIONS)
    assert normalized["overall_scores"][3]["level"] == 5


def test_review_schema_validates_dimension_scores() -> None:
    finding = {
        "severity": "low",
        "title": "accuracy note",
        "body": "型の前提を明示するとよい。",
        "file": "cli/example.py",
        "line_start": 1,
        "line_end": 1,
        "confidence": 0.8,
        "recommendation": "型コメントを追加する。",
        "dimension_scores": [
            {"dimension": "accuracy", "level": 3, "comment": "致命的ではない"},
            {"dimension": "maintainability", "level": 4, "comment": "影響は小さい"},
        ],
    }
    normalized = review_output.normalize_review(_base_review(findings=[finding]), _schema())
    assert normalized["findings"][0]["dimension_scores"] == [
        {"dimension": "accuracy", "level": 3, "comment": "致命的ではない"},
        {"dimension": "maintainability", "level": 4, "comment": "影響は小さい"},
    ]


def test_legacy_review_without_scores_still_validates() -> None:
    payload = _base_review()
    payload.pop("overall_scores")
    normalized = review_output.normalize_review(payload, _schema())
    assert len(normalized["overall_scores"]) == 5
    assert {score["level"] for score in normalized["overall_scores"]} == {3}


def test_helix_codex_dry_run_prepends_review_template(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    env = {
        "HOME": str(tmp_path),
        "HELIX_HOME": str(REPO_ROOT),
        "HELIX_PROJECT_ROOT": str(project_root),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
    }
    result = subprocess.run(
        [
            str(REPO_ROOT / "cli" / "helix-codex"),
            "--role",
            "tl",
            "--task",
            "レビューしてください",
            "--dry-run",
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Review Template: cli/templates/codex-review-prompt.md" in result.stdout
    assert "HELIX レビュー prompt template" in result.stdout
    assert "role=tl" in result.stdout
