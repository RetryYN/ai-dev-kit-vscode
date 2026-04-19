import json
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_dispatcher


def _write_catalog(tmp_path: Path) -> tuple[Path, Path]:
    skills_root = tmp_path / "skills"
    entries = [
        ("common", "code-review"),
        ("common", "testing"),
        ("workflow", "verification"),
        ("project", "api"),
    ]
    for category, name in entries:
        skill_md = skills_root / category / name / "SKILL.md"
        skill_md.parent.mkdir(parents=True, exist_ok=True)
        skill_md.write_text(
            "---\n"
            f"name: {name}\n"
            f"description: {name}\n"
            "metadata:\n"
            "  helix_layer: L4\n"
            "compatibility:\n"
            "  claude: true\n"
            "  codex: true\n"
            "---\n",
            encoding="utf-8",
        )

    catalog = {
        "version": "1.0",
        "generated_at": "2026-01-01T00:00:00Z",
        "skill_count": len(entries),
        "reference_count": 0,
        "skills": [
            {
                "id": f"{category}/{name}",
                "name": name,
                "category": category,
                "path": f"skills/{category}/{name}/SKILL.md",
                "description": name,
                "helix_layer": "L4",
                "triggers": [],
                "verification": [],
                "compatibility": {"claude": True, "codex": True},
                "references": [],
            }
            for category, name in entries
        ],
    }
    catalog_path = tmp_path / "skill-catalog.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return skills_root, catalog_path


def _insert_usage(
    db_path: Path,
    skill_id: str,
    outcome: str = "delegated",
    created_at: str = "2026-04-19 00:00:00",
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        skill_dispatcher._ensure_db_schema(conn)  # noqa: SLF001
        conn.execute(
            "INSERT INTO skill_usage (task_text, skill_id, outcome, created_at) VALUES (?, ?, ?, ?)",
            ("task", skill_id, outcome, created_at),
        )
        conn.commit()
    finally:
        conn.close()


def test_stats_includes_diversity_metrics(tmp_path: Path) -> None:
    skills_root, catalog_path = _write_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    for _ in range(4):
        _insert_usage(db_path, "common/code-review", "delegated")
    _insert_usage(db_path, "common/testing", "failed")

    result = skill_dispatcher.stats(
        db_path=db_path,
        days=30,
        catalog_path=catalog_path,
        skills_root=skills_root,
    )

    assert result["total"] == 5
    assert result["success_rate"] == 0.8
    assert result["top_skills"][0] == {"skill_id": "common/code-review", "count": 4}
    assert result["by_category"] == {"common": 5}

    diversity = result["diversity"]
    assert diversity["unique_skills_used"] == 2
    assert diversity["total_skills"] == 4
    assert diversity["coverage_rate"] == 0.5
    assert diversity["top_skill_share"] == 0.8
    assert diversity["top_skill_id"] == "common/code-review"
    assert diversity["category_count"] == 1
    assert diversity["total_categories"] == 3
    assert round(diversity["gini_coefficient"], 3) == 0.65
    assert diversity["gini_label"] == "偏り大"


def test_stats_empty_db_returns_zeroed_diversity(tmp_path: Path) -> None:
    skills_root, catalog_path = _write_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    result = skill_dispatcher.stats(
        db_path=db_path,
        days=30,
        catalog_path=catalog_path,
        skills_root=skills_root,
    )

    assert result["total"] == 0
    assert result["top_skills"] == []
    assert result["by_category"] == {}

    diversity = result["diversity"]
    assert diversity["unique_skills_used"] == 0
    assert diversity["total_skills"] == 4
    assert diversity["coverage_rate"] == 0.0
    assert diversity["gini_coefficient"] == 0.0
    assert diversity["gini_label"] == "均等"
    assert diversity["top_skill_share"] == 0.0
    assert diversity["top_skill_id"] == ""
    assert diversity["category_count"] == 0
    assert diversity["total_categories"] == 3
