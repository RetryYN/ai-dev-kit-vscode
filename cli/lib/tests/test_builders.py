"""builders/ (BuilderStore, BuilderHistory, BuilderRegistry) のテスト。"""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from builders.store import BuilderStore
from builders.history import BuilderHistory
from builders.registry import BuilderRegistry
from builders.base import BuilderBase


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


# ---------------------------------------------------------------------------
# BuilderStore
# ---------------------------------------------------------------------------

class TestBuilderStore:
    def test_init_creates_db(self, tmp_path: Path) -> None:
        db = _db_path(tmp_path)
        store = BuilderStore(db)
        assert Path(db).exists()

    def test_create_execution_returns_id(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution(
            builder_type="task",
            task_id="t-001",
            input_params={"key": "value"},
            schema_version="1.0",
        )
        assert eid.startswith("be-")

    def test_get_execution_returns_data(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution("task", "t-001", {"x": 1}, "1.0")
        data = store.get_execution(eid)
        assert data["execution_id"] == eid
        assert data["builder_type"] == "task"
        assert data["status"] == "running"

    def test_get_execution_not_found_raises(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        with pytest.raises(ValueError, match="not found"):
            store.get_execution("nonexistent")

    def test_add_step_increments_count(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution("task", "t-001", {}, "1.0")
        store.add_step(eid, "step-1", {"info": "test"})
        store.add_step(eid, "step-2", {"info": "test2"})
        data = store.get_execution(eid)
        assert data["step_count"] == 2
        assert data["current_step"] == "step-2"

    def test_add_step_nonexistent_raises(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        with pytest.raises(ValueError, match="not found"):
            store.add_step("nonexistent", "step-1", {})

    def test_finish_execution_success(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution("task", "t-001", {}, "1.0")
        store.finish_execution(
            eid,
            success=True,
            artifacts=[{"path": "out.json"}],
            validation={"quality_score": 85.0},
            error=None,
        )
        data = store.get_execution(eid)
        assert data["status"] == "completed"
        assert data["success"] == 1
        assert data["quality_score"] == 85.0

    def test_finish_execution_failure(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution("task", "t-001", {}, "1.0")
        store.finish_execution(
            eid,
            success=False,
            artifacts=[],
            validation={},
            error="something broke",
        )
        data = store.get_execution(eid)
        assert data["status"] == "failed"
        assert data["success"] == 0
        assert data["error_text"] == "something broke"

    def test_list_executions_filters_by_type(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        store.create_execution("task", "t-001", {}, "1.0")
        store.create_execution("agent", "a-001", {}, "1.0")
        store.create_execution("task", "t-002", {}, "1.0")

        results = store.list_executions("task", success_only=False, limit=10)
        assert len(results) == 2
        assert all(r["builder_type"] == "task" for r in results)

    def test_list_executions_success_only(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid1 = store.create_execution("task", "t-001", {}, "1.0")
        eid2 = store.create_execution("task", "t-002", {}, "1.0")
        store.finish_execution(eid1, success=True, artifacts=[], validation={}, error=None)
        store.finish_execution(eid2, success=False, artifacts=[], validation={}, error="err")

        results = store.list_executions("task", success_only=True, limit=10)
        assert len(results) == 1
        assert results[0]["execution_id"] == eid1

    def test_redaction_in_step_data(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution("task", "t-001", {}, "1.0")
        store.add_step(eid, "step-secret", {"password": "hunter2", "safe": "ok"})
        data = store.get_execution(eid)
        trace = data.get("step_trace", [])
        assert len(trace) == 1
        assert trace[0]["data"]["password"] == "[REDACTED]"
        assert trace[0]["data"]["safe"] == "ok"


# ---------------------------------------------------------------------------
# BuilderHistory
# ---------------------------------------------------------------------------

class TestBuilderHistory:
    def test_search_returns_scored_results(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        eid = store.create_execution(
            "task", "t-001",
            {"pattern_tags": ["role:tl", "skill:design"]},
            "1.0",
        )
        store.finish_execution(eid, success=True, artifacts=[], validation={"quality_score": 90}, error=None)

        history = BuilderHistory(store)
        results = history.search(
            "task",
            {"pattern_tags": ["role:tl", "skill:design"]},
            limit=5,
        )
        assert len(results) >= 1
        assert "_score" in results[0]

    def test_search_empty_history(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        history = BuilderHistory(store)
        results = history.search("task", {}, limit=5)
        assert results == []

    def test_search_recipe_candidates_scoring(self) -> None:
        candidates = [
            {
                "pattern_key": "api-crud",
                "recipe_id": "r-1",
                "classification": {"tags": ["api", "crud"]},
                "metrics": {"quality_score": 80},
            },
            {
                "pattern_key": "db-migration",
                "recipe_id": "r-2",
                "classification": {"tags": ["db"]},
                "metrics": {"quality_score": 60},
            },
        ]
        results = BuilderHistory.search_recipe_candidates("api", candidates, limit=2)
        assert len(results) == 2
        assert results[0]["pattern_key"] == "api-crud"  # api matches better

    def test_search_recipe_candidates_empty_query(self) -> None:
        candidates = [
            {
                "pattern_key": "test-pattern",
                "classification": {"tags": ["a", "b"]},
                "metrics": {"quality_score": 50},
            },
        ]
        results = BuilderHistory.search_recipe_candidates("", candidates, limit=5)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# BuilderRegistry
# ---------------------------------------------------------------------------

class TestBuilderRegistry:
    def setup_method(self) -> None:
        """テスト間で registry をクリアする。"""
        BuilderRegistry._builders = {}

    def test_register_and_get(self) -> None:
        class MyBuilder:
            BUILDER_TYPE = "my-builder"

        BuilderRegistry.register(MyBuilder)
        assert BuilderRegistry.get("my-builder") is MyBuilder

    def test_register_without_type_raises(self) -> None:
        class BadBuilder:
            BUILDER_TYPE = ""

        with pytest.raises(ValueError, match="BUILDER_TYPE"):
            BuilderRegistry.register(BadBuilder)

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown"):
            BuilderRegistry.get("nonexistent")

    def test_list_types(self) -> None:
        class BuilderA:
            BUILDER_TYPE = "alpha"

        class BuilderB:
            BUILDER_TYPE = "beta"

        BuilderRegistry.register(BuilderA)
        BuilderRegistry.register(BuilderB)
        types = BuilderRegistry.list_types()
        assert types == ["alpha", "beta"]

    def test_list_types_empty(self) -> None:
        assert BuilderRegistry.list_types() == []


# ---------------------------------------------------------------------------
# BuilderBase
# ---------------------------------------------------------------------------

class TestBuilderBase:
    def test_start_requires_builder_type(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        base = BuilderBase(store, str(tmp_path))
        # BUILDER_TYPE is empty string by default
        with pytest.raises(ValueError, match="BUILDER_TYPE"):
            base.start("t-001", {})

    def test_step_before_start_raises(self, tmp_path: Path) -> None:
        store = BuilderStore(_db_path(tmp_path))
        base = BuilderBase(store, str(tmp_path))
        with pytest.raises(RuntimeError, match="not started"):
            base.step("test-step", {})
