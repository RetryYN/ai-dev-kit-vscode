import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import code_catalog
import entry_helper
import effort_classifier
import skill_classifier
from skill_recommender import SkillRecommender


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    return db_path


def _git_add(root: Path, *paths: str) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", *paths], cwd=root, check=True, capture_output=True)


def _rebuild_catalog(root: Path) -> Path:
    db_path = root / ".helix" / "helix.db"
    jsonl_path = root / ".helix" / "cache" / "code-catalog.jsonl"
    code_catalog.rebuild_catalog(root, jsonl_path, db_path)
    return db_path


def test_migrate_v16_to_v17_creates_entries_links_tables(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        entry_cols = [row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()]
        link_cols = [row["name"] for row in conn.execute("PRAGMA table_info(links)").fetchall()]
    finally:
        conn.close()

    assert entry_cols == [
        "id",
        "axis",
        "stack",
        "lifecycle",
        "parent_entry_id",
        "sprint_id",
        "agent_actor",
        "ref",
        "version",
        "metadata",
        "created_at",
        "updated_at",
        "qa_result",
        "security_audit",
        "design_decision",
    ]
    assert link_cols == ["from_id", "to_id", "kind", "metadata"]


def test_migrate_v16_to_v17_creates_indexes(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        entry_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(entries)").fetchall()}
        link_indexes = {row["name"] for row in conn.execute("PRAGMA index_list(links)").fetchall()}
    finally:
        conn.close()

    assert {name for name in entry_indexes if name.startswith("idx_entries_")} == {
        "idx_entries_axis",
        "idx_entries_stack",
        "idx_entries_sprint",
        "idx_entries_agent",
        "idx_entries_lifecycle",
    }
    assert {name for name in link_indexes if name.startswith("idx_links_")} == {"idx_links_kind"}


def test_migrate_v16_to_v17_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    helix_db.init_db(db_path)

    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM schema_version WHERE version = 17").fetchone()
    finally:
        conn.close()

    assert row["count"] == 1


def test_entries_axis_check_constraint(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('x', 'invalid', 'initial', 'r')"
            )
    finally:
        conn.close()


def test_links_fk_cascade_on_entry_delete(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('from_x', 'code', 'initial', 'rf')")
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('to_x', 'code', 'initial', 'rt')")
        conn.execute("INSERT INTO links (from_id, to_id, kind) VALUES ('from_x', 'to_x', 'uses')")
        conn.execute("DELETE FROM entries WHERE id = 'from_x'")
        row = conn.execute("SELECT COUNT(*) AS count FROM links").fetchone()
    finally:
        conn.close()

    assert row["count"] == 0


def test_entries_lifecycle_check_constraint(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('x', 'code', 'unknown', 'r')"
            )
    finally:
        conn.close()


def test_links_kind_check_constraint(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('from_x', 'code', 'initial', 'rf')")
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('to_x', 'code', 'initial', 'rt')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO links (from_id, to_id, kind) VALUES ('from_x', 'to_x', 'invalid')")
    finally:
        conn.close()


def test_entries_parent_fk_set_null_on_delete(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        conn.execute("INSERT INTO entries (id, axis, lifecycle, ref) VALUES ('parent_x', 'design', 'initial', 'rp')")
        conn.execute(
            """
            INSERT INTO entries (id, axis, lifecycle, parent_entry_id, ref)
            VALUES ('child_x', 'design', 'addition', 'parent_x', 'rc')
            """
        )
        conn.execute("DELETE FROM entries WHERE id = 'parent_x'")
        row = conn.execute("SELECT parent_entry_id FROM entries WHERE id = 'child_x'").fetchone()
    finally:
        conn.close()

    assert row["parent_entry_id"] is None


def test_migrate_v17_to_v18_extends_code_index(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        code_index_cols = [row["name"] for row in conn.execute("PRAGMA table_info(code_index)").fetchall()]
    finally:
        conn.close()

    assert code_index_cols == [
        "id",
        "domain",
        "summary",
        "path",
        "line_no",
        "symbol_line",
        "since",
        "related",
        "source_hash",
        "bucket",
        "updated_at",
        "axis",
        "stack",
        "lifecycle",
        "parent_entry_id",
        "sprint_id",
        "agent_actor",
    ]


def test_migrate_v17_to_v18_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "helix.db"
    helix_db.init_db(db_path)
    helix_db.init_db(db_path)

    conn = helix_db.get_connection(db_path)
    try:
        version_row = conn.execute("SELECT COUNT(*) AS count FROM schema_version WHERE version = 18").fetchone()
        code_index_cols = [row["name"] for row in conn.execute("PRAGMA table_info(code_index)").fetchall()]
    finally:
        conn.close()

    assert version_row["count"] == 1
    assert len(code_index_cols) == 17


def test_sync_to_db_populates_entries_for_code_axis(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "# @helix:index id=foo.bar domain=cli/lib summary=test\n"
        "def foo():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    _git_add(tmp_path, "sample.py")

    db_path = _rebuild_catalog(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        code_row = conn.execute("SELECT COUNT(*) AS count FROM code_index WHERE id = 'foo.bar'").fetchone()
        entry_row = conn.execute("SELECT axis, lifecycle FROM entries WHERE id = 'foo.bar'").fetchone()
    finally:
        conn.close()

    assert code_row["count"] == 1
    assert entry_row["axis"] == "code"
    assert entry_row["lifecycle"] == "initial"


def test_sync_to_db_respects_lifecycle_field(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "# @helix:index id=foo.baz domain=cli/lib summary=test lifecycle=addition\n"
        "def foo():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    _git_add(tmp_path, "sample.py")

    db_path = _rebuild_catalog(tmp_path)
    conn = helix_db.get_connection(db_path)
    try:
        entry_row = conn.execute("SELECT lifecycle FROM entries WHERE id = 'foo.baz'").fetchone()
    finally:
        conn.close()

    assert entry_row["lifecycle"] == "addition"


def test_entry_helper_coverage_triplet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(db_path)

    conn = helix_db.get_connection(db_path)
    try:
        conn.executemany(
            """
            INSERT INTO entries (id, axis, stack, lifecycle, ref)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("design.initial.1", "design", "front", "initial", "docs/design-1.md"),
                ("design.initial.2", "design", "front", "initial", "docs/design-2.md"),
                ("code.modified", "code", "back", "modification", "cli/lib/foo.py"),
                ("test.added", "test", None, "addition", "cli/lib/tests/test_foo.py"),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    capsys.readouterr()
    assert entry_helper.dispatch("coverage", ["--triplet", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    rows = {
        (item["axis"], item["stack"], item["lifecycle"]): item
        for item in payload["triplet"]
    }
    assert rows[("design", "front", "initial")]["count"] == 2
    assert rows[("design", "front", "initial")]["ratio"] == pytest.approx(0.5)
    assert rows[("code", "back", "modification")]["count"] == 1
    assert rows[("code", "back", "modification")]["ratio"] == pytest.approx(0.25)
    assert rows[("test", "n/a", "addition")]["count"] == 1
    assert rows[("test", "n/a", "addition")]["ratio"] == pytest.approx(0.25)


def _w2d_fetch_metadata(db_path: Path, classifier_name: str) -> dict:
    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT metadata FROM entries WHERE id LIKE ?",
            (f"{classifier_name}.%",),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return json.loads(row["metadata"])


def _w2d_recommender(tmp_path: Path, db_path: Path) -> SkillRecommender:
    classifier = SkillRecommender(db_path=db_path)
    classifier.cache_dir = tmp_path / "recommend-cache"
    classifier._top_n = 1
    classifier._task_text = "entries test"
    return classifier


def _w2d_recommendation_json(skill_id: str = "common/testing") -> str:
    return json.dumps(
        {
            "recommendations": [
                {
                    "skill_id": skill_id,
                    "score": 0.91,
                    "reason": "entries integration",
                    "recommended_agent": "qa",
                }
            ]
        },
        ensure_ascii=False,
    )


def test_classifiers_records_metadata_contains_query_and_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = _init_db(tmp_path)

    recommender = _w2d_recommender(tmp_path, db_path)
    monkeypatch.setattr(recommender, "_invoke_codex", lambda query, context: _w2d_recommendation_json())
    recommender.classify("entries recommender", {"prompt": "p", "top_n": 1})

    effort = effort_classifier.EffortClassifier(db_path=db_path)
    effort.cache_dir = tmp_path / "effort-cache"
    effort.classify("entries effort", role="qa", size="S", files=1, lines=1, use_llm=False)

    classifier = skill_classifier.SkillClassifier(db_path=db_path)
    classifier.cache_dir = tmp_path / "skill-classifier-cache"
    monkeypatch.setattr(
        classifier,
        "_invoke_codex",
        lambda query, context: (
            '{"phases":["L2"],"tasks":["design-api"],"triggers":["API"],'
            '"anti_triggers":[],"agent":"tl","similar":[],"confidence":0.8}'
        ),
    )
    classifier.classify_skill(
        "common/security",
        "# SKILL",
        known_task_ids={"design-api"},
        allowed_agents={"tl"},
        allowed_phases={"L2"},
    )

    expectations = {
        "skill_recommender": "entries recommender",
        "effort_classifier": "entries effort",
        "skill_classifier": "common/security",
    }
    for classifier_name, query in expectations.items():
        metadata = _w2d_fetch_metadata(db_path, classifier_name)
        assert metadata["query"] == query
        assert isinstance(metadata["result"], dict)
        assert metadata["source"] in {"codex", "rule"}


def test_classifier_cache_hit_skips_codex_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _init_db(tmp_path)
    classifier = _w2d_recommender(tmp_path, db_path)
    calls = {"invoke": 0}

    def _fake_invoke(query: str, context: dict | None) -> str:
        calls["invoke"] += 1
        return _w2d_recommendation_json()

    monkeypatch.setattr(classifier, "_invoke_codex", _fake_invoke)

    first = classifier.classify("same query", {"prompt": "p", "top_n": 1})
    second = classifier.classify("same query", {"prompt": "p", "top_n": 1})

    assert first == second
    assert calls["invoke"] == 1


def test_classifier_cache_miss_invokes_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _init_db(tmp_path)
    classifier = _w2d_recommender(tmp_path, db_path)
    calls = {"invoke": 0}

    def _fake_invoke(query: str, context: dict | None) -> str:
        calls["invoke"] += 1
        return _w2d_recommendation_json(f"common/testing-{calls['invoke']}")

    monkeypatch.setattr(classifier, "_invoke_codex", _fake_invoke)

    classifier.classify("query one", {"prompt": "p", "top_n": 1})
    classifier.classify("query two", {"prompt": "p", "top_n": 1})

    assert calls["invoke"] == 2
