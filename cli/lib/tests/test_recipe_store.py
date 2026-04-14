import json
import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import recipe_store


MODULE_PATH = LIB_DIR / "recipe_store.py"


def _recipe_dir(project_root: Path) -> Path:
    path = project_root / ".helix" / "recipes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_recipe(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_list_recipes_skips_invalid_and_non_dict_payloads(tmp_path: Path) -> None:
    recipe_dir = _recipe_dir(tmp_path)
    (recipe_dir / "broken.json").write_text("{oops", encoding="utf-8")
    _write_recipe(recipe_dir / "array.json", ["not-a-dict"])
    valid_path = _write_recipe(recipe_dir / "valid.json", {"recipe_id": "recipe-valid"})

    recipes = recipe_store.list_recipes(str(tmp_path))

    assert len(recipes) == 1
    assert recipes[0]["recipe_id"] == "recipe-valid"
    assert recipes[0]["_path"] == str(valid_path)


def test_from_history_returns_ranked_recommendations(tmp_path: Path) -> None:
    recipe_dir = _recipe_dir(tmp_path)
    _write_recipe(
        recipe_dir / "best.json",
        {
            "recipe_id": "recipe-best",
            "summary": "pytest regression for qa flows",
            "pattern_key": "review-security::pytest",
            "classification": {
                "task_type": "review-security",
                "role": "qa",
                "builder_type": "task",
                "tags": ["pytest", "qa"],
            },
            "metrics": {"quality_score": 95},
            "notes": {"why_it_worked": "stable regression"},
        },
    )
    _write_recipe(
        recipe_dir / "other.json",
        {
            "recipe_id": "recipe-other",
            "summary": "docs workflow",
            "classification": {"role": "docs", "tags": ["docs"]},
            "metrics": {"quality_score": 40},
        },
    )

    result = recipe_store.from_history("qa pytest", str(tmp_path), limit=1)

    assert result["query"] == "qa pytest"
    assert [item["recipe_id"] for item in result["recommendations"]] == ["recipe-best"]
    assert result["warnings"] == []
    assert result["failure_recipes"] == []


def test_from_history_returns_redacted_warning_for_failure_recipe(tmp_path: Path) -> None:
    recipe_dir = _recipe_dir(tmp_path)
    _write_recipe(
        recipe_dir / "failed.json",
        {
            "recipe_id": "recipe-failed",
            "failure_type": "auth-error",
            "success": False,
            "classification": {"role": "qa", "tags": ["token", "failure"]},
            "notes": {"failure_reason": "token=super-secret should not leak"},
            "source": {"output_log": "token=backup"},
        },
    )

    result = recipe_store.from_history("token failure", str(tmp_path), limit=2)

    assert result["recommendations"] == []
    assert len(result["warnings"]) == 1
    assert "[REDACTED]" in result["warnings"][0]
    assert result["failure_recipes"][0]["warning"] == result["warnings"][0]


def test_load_recipe_prefers_project_local_over_user_global(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_recipe = _write_recipe(
        _recipe_dir(tmp_path) / "shared.json",
        {"recipe_id": "shared", "summary": "project-local"},
    )
    fake_home = tmp_path / "fake-home"
    _write_recipe(
        fake_home / ".helix" / "recipes" / "shared.json",
        {"recipe_id": "shared", "summary": "user-global"},
    )
    monkeypatch.setattr(recipe_store.Path, "home", staticmethod(lambda: fake_home))

    loaded = recipe_store.load_recipe("shared", str(tmp_path))

    assert loaded is not None
    assert loaded["summary"] == "project-local"
    assert loaded["_path"] == str(project_recipe)


def test_find_recipe_is_alias_of_load_recipe(tmp_path: Path) -> None:
    recipe_path = _write_recipe(
        _recipe_dir(tmp_path) / "alias.json",
        {"recipe_id": "alias", "summary": "alias works"},
    )

    loaded = recipe_store.find_recipe("alias", str(tmp_path))

    assert loaded is not None
    assert loaded["recipe_id"] == "alias"
    assert loaded["_path"] == str(recipe_path)
