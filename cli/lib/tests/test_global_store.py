"""global_store.py のテスト。"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import global_store


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _set_global_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """HELIX_GLOBAL_HOME を tmp_path に向ける。"""
    home = tmp_path / "global_home"
    monkeypatch.setenv("HELIX_GLOBAL_HOME", str(home))
    return home


# ---------------------------------------------------------------------------
# init_global_db
# ---------------------------------------------------------------------------

class TestInitGlobalDb:
    def test_creates_db_and_dirs(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        home = _set_global_home(monkeypatch, tmp_path)
        db_path = global_store.init_global_db()
        assert Path(db_path).exists()
        assert (home / "recipes").is_dir()

    def test_idempotent(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _set_global_home(monkeypatch, tmp_path)
        path1 = global_store.init_global_db()
        path2 = global_store.init_global_db()
        assert path1 == path2


# ---------------------------------------------------------------------------
# search_global (空 DB)
# ---------------------------------------------------------------------------

class TestSearchGlobalEmpty:
    def test_empty_db_returns_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _set_global_home(monkeypatch, tmp_path)
        results = global_store.search_global("anything")
        assert isinstance(results, list)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# get_recipe_by_id
# ---------------------------------------------------------------------------

class TestGetRecipeById:
    def test_missing_returns_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _set_global_home(monkeypatch, tmp_path)
        assert global_store.get_recipe_by_id("nonexistent") is None

    def test_empty_id_returns_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _set_global_home(monkeypatch, tmp_path)
        assert global_store.get_recipe_by_id("") is None


# ---------------------------------------------------------------------------
# get_promotion_candidates
# ---------------------------------------------------------------------------

class TestGetPromotionCandidates:
    def test_empty_db_returns_empty(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _set_global_home(monkeypatch, tmp_path)
        candidates = global_store.get_promotion_candidates(threshold=1)
        assert candidates == []


# ---------------------------------------------------------------------------
# record_promotion
# ---------------------------------------------------------------------------

class TestRecordPromotion:
    def test_creates_promotion_record(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _set_global_home(monkeypatch, tmp_path)
        global_store.init_global_db()
        promotion_id = global_store.record_promotion(
            recipe_id="test-recipe",
            artifact_type="skill",
            builder_type="task",
            artifact_ref="ref-001",
            status="promoted",
            project_id="proj-1",
        )
        assert promotion_id.startswith("promo-")

        # Verify in DB
        db_path = global_store.init_global_db()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM promotion_records WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["recipe_id"] == "test-recipe"
        assert row["status"] == "promoted"


# ---------------------------------------------------------------------------
# _sanitize_recipe
# ---------------------------------------------------------------------------

class TestSanitizeRecipe:
    def test_redacts_secret_keys(self) -> None:
        recipe = {"name": "test", "api_key": "sk-12345", "data": "ok"}
        sanitized = global_store._sanitize_recipe(recipe)
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["name"] == "test"
        assert sanitized["data"] == "ok"

    def test_redacts_nested_secrets(self) -> None:
        recipe = {"config": {"password": "hunter2"}}
        sanitized = global_store._sanitize_recipe(recipe)
        assert sanitized["config"]["password"] == "[REDACTED]"

    def test_redacts_home_path_in_values(self) -> None:
        recipe = {"path": "/home/user/.secret/key"}
        sanitized = global_store._sanitize_recipe(recipe)
        assert sanitized["path"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# _tokenize_query
# ---------------------------------------------------------------------------

class TestTokenizeQuery:
    def test_splits_on_spaces_and_commas(self) -> None:
        tokens = global_store._tokenize_query("api, db auth")
        assert tokens == ["api", "db", "auth"]

    def test_empty_string(self) -> None:
        assert global_store._tokenize_query("") == []

    def test_none_input(self) -> None:
        assert global_store._tokenize_query(None) == []


# ---------------------------------------------------------------------------
# _score_global_row
# ---------------------------------------------------------------------------

class TestScoreGlobalRow:
    def test_score_without_tokens(self) -> None:
        row = {
            "pattern_key": "api-crud",
            "tags": ["api", "crud"],
            "success_count": 5,
            "quality_score_mean": 80.0,
            "verification": {},
        }
        score = global_store._score_global_row([], row)
        assert score > 0.0

    def test_score_with_matching_tokens(self) -> None:
        row = {
            "pattern_key": "api-crud",
            "tags": ["api", "crud"],
            "success_count": 5,
            "quality_score_mean": 80.0,
            "verification": {},
        }
        score_match = global_store._score_global_row(["api"], row)
        score_no_match = global_store._score_global_row(["zzz"], row)
        assert score_match > score_no_match
