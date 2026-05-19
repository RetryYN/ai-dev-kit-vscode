import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_dispatcher


def _ts_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


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
    created_at: str | None = None,
    session_id: str | None = None,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        skill_dispatcher._ensure_db_schema(conn)  # noqa: SLF001
        if created_at is None:
            created_at = _ts_days_ago(1)
        conn.execute(
            "INSERT INTO skill_usage (task_text, skill_id, outcome, created_at, session_id) "
            "VALUES (?, ?, ?, ?, ?)",
            ("task", skill_id, outcome, created_at, session_id),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_session(
    db_path: Path,
    session_id: str,
    started_at: str | None = None,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        skill_dispatcher._ensure_db_schema(conn)  # noqa: SLF001
        if started_at is None:
            started_at = _ts_days_ago(1)
        conn.execute(
            "INSERT INTO sessions (id, started_at) VALUES (?, ?)",
            (session_id, started_at),
        )
        conn.commit()
    finally:
        conn.close()


def _fetch_usage(db_path: Path, usage_id: int) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM skill_usage WHERE id = ?", (usage_id,)).fetchone()
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
    assert result["hit_rate"] == (1 / 30 * 100)


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
    assert result["hit_rate"] == 0.0
    assert result["active_sessions"] == 0
    assert result["total_sessions"] == 0


def test_stats_includes_hit_rate(tmp_path: Path) -> None:
    skills_root, catalog_path = _write_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    _insert_usage(db_path, "common/code-review", "delegated", _ts_days_ago(2))
    _insert_usage(db_path, "common/testing", "delegated", _ts_days_ago(1))

    result = skill_dispatcher.stats(
        db_path=db_path,
        days=30,
        catalog_path=catalog_path,
        skills_root=skills_root,
    )

    assert "hit_rate" in result
    assert isinstance(result["hit_rate"], (int, float))
    assert 0.0 <= result["hit_rate"] <= 100.0
    assert round(result["hit_rate"], 2) == round((2 / 30) * 100, 2)
    assert result["active_sessions"] == 0
    assert result["total_sessions"] == 0


def test_stats_hit_rate_sessions_based(tmp_path: Path) -> None:
    skills_root, catalog_path = _write_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    for i in range(10):
        _insert_session(db_path, f"session-{i}", _ts_days_ago(1))
    for i in range(3):
        _insert_usage(
            db_path,
            "common/code-review",
            "delegated",
            _ts_days_ago(1),
            session_id=f"session-{i}",
        )

    result = skill_dispatcher.stats(
        db_path=db_path,
        days=30,
        catalog_path=catalog_path,
        skills_root=skills_root,
    )

    assert result["active_sessions"] == 3
    assert result["total_sessions"] == 10
    assert result["hit_rate"] == 30.0


def test_stats_hit_rate_falls_back_to_days(tmp_path: Path) -> None:
    skills_root, catalog_path = _write_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    _insert_session(db_path, "session-legacy", _ts_days_ago(31))
    _insert_usage(db_path, "common/code-review", "delegated", _ts_days_ago(2))
    _insert_usage(db_path, "common/testing", "delegated", _ts_days_ago(1))

    result = skill_dispatcher.stats(
        db_path=db_path,
        days=30,
        catalog_path=catalog_path,
        skills_root=skills_root,
    )

    assert result["active_sessions"] == 0
    assert result["total_sessions"] == 0
    assert round(result["hit_rate"], 2) == round((2 / 30) * 100, 2)


def test_stats_records_session_id_when_env_set(monkeypatch, tmp_path: Path) -> None:
    skills_root, catalog_path = _write_catalog(tmp_path)
    db_path = tmp_path / ".helix" / "helix.db"

    monkeypatch.setenv("HELIX_SESSION_ID", "session-from-env")

    result = skill_dispatcher.dispatch(
        skill_id="common/testing",
        task_text="native task",
        recommended_agent="@be-api",
        references=[],
        catalog_path=catalog_path,
        skills_root=skills_root,
        db_path=db_path,
        dry_run=False,
    )

    row = _fetch_usage(db_path, int(result["usage_id"]))
    assert row["session_id"] == "session-from-env"
