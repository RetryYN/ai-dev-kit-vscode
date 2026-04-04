import json
import sqlite3
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import learning_engine


@pytest.fixture(autouse=True)
def clear_verification_cache() -> None:
    learning_engine._VERIFICATION_CACHE.clear()


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".helix").mkdir(parents=True, exist_ok=True)
    return root


def _db_path(tmp_path: Path) -> Path:
    root = _project_root(tmp_path)
    db_path = root / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _insert_success_run(db_path: Path, status: str = "completed") -> int:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO task_runs (task_id, task_type, plan_goal, role, status, started_at, completed_at, output_log)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "T777",
            "review-security",
            "handle secret=abc123 safely",
            "qa",
            status,
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:05:00Z",
            "Results: 4 passed, 0 failed",
        ),
    )
    run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.executemany(
        """
        INSERT INTO action_logs (task_run_id, action_index, action_type, action_desc, status, evidence)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (run_id, 1, "search-external", "query=q token=secret-token", "passed", '{"token":"abc"}'),
            (run_id, 2, "pytest", "run pytest", "passed", "Results: 4 passed, 0 failed"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO observations (task_run_id, action_log_id, action_type, expected_keywords, matched_keywords, passed, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (run_id, None, "search-external", '["query"]', '["query"]', 1, ""),
            (run_id, None, "pytest", '["passed"]', '["passed"]', 0, "one check failed"),
        ],
    )
    conn.commit()
    conn.close()
    return run_id


def _fake_verification() -> dict:
    return {
        "tests": {"total": 4, "passed": 4, "failed": 0, "coverage": 87.5, "test_files": []},
        "contracts": {"api_diff": "not found", "type_check": "not detected", "schema_valid": None},
        "quality": {"lint_errors": 0, "security_issues": 0, "textlint_errors": -1},
        "collected_at": "2025-01-01T00:00:00Z",
    }


def test_build_pattern_key_is_deterministic() -> None:
    key1 = learning_engine._build_pattern_key("review-security", ["search", "pytest"])
    key2 = learning_engine._build_pattern_key("review-security", ["search", "pytest"])

    assert key1 == key2


def test_build_pattern_key_changes_when_action_order_changes() -> None:
    key1 = learning_engine._build_pattern_key("review-security", ["search", "pytest"])
    key2 = learning_engine._build_pattern_key("review-security", ["pytest", "search"])

    assert key1 != key2


def test_analyze_success_raises_for_missing_task_run(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)

    with pytest.raises(ValueError, match="task_run_id not found"):
        learning_engine.analyze_success(999, str(db_path))


def test_analyze_success_raises_for_non_completed_task(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    run_id = _insert_success_run(db_path, status="running")

    with pytest.raises(ValueError, match="not successful"):
        learning_engine.analyze_success(run_id, str(db_path))


def test_analyze_success_returns_none_when_run_has_no_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = _db_path(tmp_path)
    monkeypatch.setattr(learning_engine, "_collect_verification", lambda _root: _fake_verification())
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO task_runs (task_id, task_type, plan_goal, role, status, started_at, completed_at, output_log)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("T001", "review-security", "goal", "qa", "completed", "2025-01-01", "2025-01-01", ""),
    )
    run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.commit()
    conn.close()

    assert learning_engine.analyze_success(run_id, str(db_path)) is None


def test_analyze_success_aggregates_metrics_and_redacts_sensitive_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = _db_path(tmp_path)
    run_id = _insert_success_run(db_path)
    monkeypatch.setattr(learning_engine, "_collect_verification", lambda _root: _fake_verification())

    recipe = learning_engine.analyze_success(run_id, str(db_path))

    assert recipe is not None
    assert recipe["source"]["task_run_id"] == run_id
    assert recipe["metrics"]["action_count"] == 2
    assert recipe["metrics"]["action_pass_rate"] == 1.0
    assert recipe["metrics"]["observation_pass_rate"] == 0.5
    assert recipe["classification"]["role"] == "qa"
    assert recipe["security"]["redacted_fields"] >= 1
    assert recipe["steps"][0]["parameters"]["token"] == "[REDACTED]"
    assert recipe["source"]["plan_goal"] == "[REDACTED]"
    assert recipe["verification"]["tests"]["coverage"] == 87.5


def test_save_recipe_writes_json_and_list_recipes_reads_it(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    recipe = {
        "recipe_id": "recipe-fixed-id",
        "pattern_key": "review::pytest::abc123",
        "classification": {"builder_type": "task", "tags": ["task:review"]},
        "metrics": {"quality_score": 90},
        "notes": {"why_it_worked": "stable"},
    }

    output_path = learning_engine.save_recipe(recipe, str(project_root))
    recipes = learning_engine.list_recipes(str(project_root))

    assert Path(output_path).exists()
    assert recipes[0]["recipe_id"] == "recipe-fixed-id"
    assert recipes[0]["_path"] == output_path


def test_save_recipe_generates_recipe_id_when_missing(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    recipe = {
        "pattern_key": "review::pytest::abc123",
        "classification": {"builder_type": "task", "tags": ["task:review"]},
        "metrics": {"quality_score": 85},
        "notes": {"why_it_worked": "stable"},
    }

    output_path = learning_engine.save_recipe(recipe, str(project_root))

    assert recipe["recipe_id"].startswith("recipe-")
    assert Path(output_path).name == f"{recipe['recipe_id']}.json"


def test_list_recipes_skips_invalid_json_and_non_dict_payloads(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    recipe_dir = project_root / ".helix" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    (recipe_dir / "bad.json").write_text("{broken", encoding="utf-8")
    (recipe_dir / "list.json").write_text('["not-a-dict"]', encoding="utf-8")
    (recipe_dir / "ok.json").write_text('{"recipe_id":"recipe-ok"}', encoding="utf-8")

    recipes = learning_engine.list_recipes(str(project_root))

    assert len(recipes) == 1
    assert recipes[0]["recipe_id"] == "recipe-ok"


def test_from_history_returns_recommendations_for_matching_query(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    learning_engine.save_recipe(
        {
            "recipe_id": "recipe-success",
            "pattern_key": "review-security::pytest::abc123",
            "classification": {
                "task_type": "review-security",
                "role": "qa",
                "builder_type": "task",
                "tags": ["task:review-security", "action:pytest"],
            },
            "metrics": {"quality_score": 92},
            "notes": {"why_it_worked": "pytest security validation"},
            "summary": "task | tags:task:review-security | success:92% | pytest security validation",
        },
        str(project_root),
    )

    result = learning_engine.from_history("security pytest", str(project_root), limit=3)

    assert result["query"] == "security pytest"
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["recipe_id"] == "recipe-success"
    assert result["warnings"] == []


def test_from_history_returns_failure_recipe_as_warning(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)
    learning_engine.save_recipe(
        {
            "recipe_id": "recipe-failure",
            "pattern_key": "review-security-failure::pytest::zzz999",
            "failure_type": "test_failure",
            "success": False,
            "classification": {
                "task_type": "review-security",
                "role": "qa",
                "builder_type": "task",
                "tags": ["task:review-security", "action:pytest"],
            },
            "metrics": {"quality_score": 10},
            "notes": {"failure_reason": "pytest failed on regression"},
        },
        str(project_root),
    )

    result = learning_engine.from_history("security pytest", str(project_root), limit=3)

    assert result["recommendations"] == []
    assert len(result["warnings"]) == 1
    assert "過去に失敗しています" in result["warnings"][0]
    assert result["failure_recipes"][0]["recipe_id"] == "recipe-failure"


def test_from_history_returns_empty_result_when_no_recipes(tmp_path: Path) -> None:
    project_root = _project_root(tmp_path)

    result = learning_engine.from_history("anything", str(project_root))

    assert result == {
        "query": "anything",
        "recommendations": [],
        "warnings": [],
        "failure_recipes": [],
    }
