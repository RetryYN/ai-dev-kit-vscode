from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cli.lib.v3.projection.secret_guard import SensitivePayloadError, assert_no_sensitive_payload
from cli.lib.v3.projection.sources import SourceEnumerationError, enumerate_source_files, load_sources
from cli.lib.v3.projection.upsert import stable_id, upsert_row
from cli.lib.v3.projection.writer import append_event, rebuild_projection
from cli.lib.v3.schema.ddl import migrate
from cli.lib.v3.schema.registry import TABLES, TABLE_BY_NAME


def _write_source(path: Path, frontmatter: dict[str, str], body: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    if body:
        lines.append(body)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _snapshot_db(conn: sqlite3.Connection) -> dict[str, list[tuple[object, ...]]]:
    snapshot: dict[str, list[tuple[object, ...]]] = {}
    for table in sorted(table.name for table in TABLES):
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        order_by = ", ".join(str(index) for index in range(1, len(columns) + 1))
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()
        snapshot[table] = rows
    return snapshot


def _fetch_rows(conn: sqlite3.Connection, table_name: str, order_by: str) -> list[tuple[object, ...]]:
    return conn.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}").fetchall()


def _build_sources_tree(root: Path) -> None:
    _write_source(
        root / "docs/plans/L7/L7-demo-plan.md",
        {
            "source_kind": "plan",
            "plan_id": "PLAN-DEMO",
            "kind": "impl",
            "layer": "L7",
            "drive": "be",
            "status": "draft",
            "updated_at": "2026-06-26T00:00:00Z",
        },
        "## body",
    )
    _write_source(
        root / "docs/v3/engine/demo-artifact.md",
        {
            "source_kind": "artifact",
            "artifact_type": "design",
            "path": "docs/v3/engine/demo-artifact.md",
            "pair_artifact": "cli/lib/v3/tests/test_projection_writer.py",
            "status": "current",
            "updated_at": "2026-06-26T00:01:00Z",
        },
        "artifact body",
    )
    _write_source(
        root / "docs/v3/engine/demo-trace.md",
        {
            "source_kind": "trace_edge",
            "from_artifact": "docs/v3/engine/demo-artifact.md",
            "to_artifact": "cli/lib/v3/tests/test_projection_writer.py",
            "edge_kind": "tests",
            "plan_id": "PLAN-DEMO",
            "status": "active",
        },
        "trace body",
    )
    _write_source(
        root / "reports/gates/G7-demo.md",
        {
            "source_kind": "gate_run",
            "gate_id": "G7",
            "plan_id": "PLAN-DEMO",
            "status": "passed",
            "checked_at": "2026-06-26T00:02:00Z",
            "evidence_path": "reports/gates/G7-demo.md",
        },
        "gate body",
    )


@pytest.fixture()
def migrated_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    try:
        yield conn
    finally:
        conn.close()


def test_ut_c2_01_rebuild_projection_is_bit_identical_for_same_sources(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-01"""
    _build_sources_tree(tmp_path)
    sources = load_sources(tmp_path)

    rebuild_projection(migrated_db, sources)
    first = _snapshot_db(migrated_db)

    rebuild_projection(migrated_db, load_sources(tmp_path))
    second = _snapshot_db(migrated_db)

    assert first == second
    assert len(_fetch_rows(migrated_db, "plan_registry", "plan_id")) == 1
    assert len(_fetch_rows(migrated_db, "artifact_registry", "artifact_id")) == 1
    assert len(_fetch_rows(migrated_db, "trace_edges", "edge_id")) == 1


def test_ut_c2_02_rebuild_truncates_projection_only(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-02"""
    _build_sources_tree(tmp_path)
    migrated_db.execute(
        "INSERT INTO plan_registry(plan_id, kind, layer, sub_doc, drive, status, parent, updated_at, decision_outcome, source_hash)"
        " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("PLAN-OLD", "impl", "L7", "", "be", "draft", "", "2026-06-25T00:00:00Z", "", ""),
    )
    migrated_db.execute(
        "INSERT INTO impact_rules(impact_rule_id, trigger_edge_kind, trigger_node_type, required_node_type, required_action, severity, gate, enabled)"
        " VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        ("RULE-1", "tests", "artifact", "plan", "review", "medium", "G4", 1),
    )
    append_event(
        migrated_db,
        {
            "table": "test_result_events",
            "ut_id": "UT-C2-02",
            "run_id": "RUN-1",
            "seq": "1",
            "status": "green",
            "run_at": "2026-06-26T00:00:00Z",
            "command": "pytest -q",
            "digest": "abc123",
        },
    )

    rebuild_projection(migrated_db, load_sources(tmp_path))

    plan_ids = {row[0] for row in _fetch_rows(migrated_db, "plan_registry", "plan_id")}
    assert plan_ids == {"PLAN-DEMO"}
    assert migrated_db.execute("SELECT count(*) FROM impact_rules").fetchone()[0] == 1
    assert migrated_db.execute("SELECT count(*) FROM test_result_events").fetchone()[0] == 1


def test_ut_c2_03_rebuild_deletes_projection_rows_when_source_is_removed(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-03"""
    artifact = _write_source(
        tmp_path / "docs/v3/engine/demo-artifact.md",
        {
            "source_kind": "artifact",
            "artifact_type": "design",
            "path": "docs/v3/engine/demo-artifact.md",
            "pair_artifact": "cli/lib/v3/tests/test_projection_writer.py",
            "status": "current",
            "updated_at": "2026-06-26T00:01:00Z",
        },
        "artifact body",
    )
    append_event(
        migrated_db,
        {
            "table": "test_result_events",
            "ut_id": "UT-C2-03",
            "run_id": "RUN-1",
            "seq": "1",
            "status": "green",
            "run_at": "2026-06-26T00:00:00Z",
            "command": "pytest -q",
            "digest": "abc123",
        },
    )

    rebuild_projection(migrated_db, load_sources(tmp_path))
    assert migrated_db.execute("SELECT count(*) FROM artifact_registry").fetchone()[0] == 1

    artifact.unlink()
    rebuild_projection(migrated_db, load_sources(tmp_path))

    assert migrated_db.execute("SELECT count(*) FROM artifact_registry").fetchone()[0] == 0
    assert migrated_db.execute("SELECT count(*) FROM test_result_events").fetchone()[0] == 1


def test_ut_c2_04_rebuild_marks_stale_rows_when_hashes_diverge(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-04"""
    _write_source(
        tmp_path / "exports/demo-artifact-v1.md",
        {
            "source_kind": "document_export",
            "export_run_id": "RUN-1",
            "format": "md",
            "path": "exports/demo-artifact.md",
            "renderer": "pandoc",
            "byte_size": "10",
            "created_at": "2026-06-26T00:00:00Z",
            "evidence_path": "exports/demo-artifact-v1.md",
        },
        "version 1",
    )
    _write_source(
        tmp_path / "exports/demo-artifact-v2.md",
        {
            "source_kind": "document_export",
            "export_run_id": "RUN-2",
            "format": "md",
            "path": "exports/demo-artifact.md",
            "renderer": "pandoc",
            "byte_size": "10",
            "created_at": "2026-06-26T00:01:00Z",
            "evidence_path": "exports/demo-artifact-v2.md",
        },
        "version 2",
    )

    rebuild_projection(migrated_db, load_sources(tmp_path))

    stale_statuses = migrated_db.execute(
        "SELECT stale_status FROM document_export_artifacts ORDER BY created_at"
    ).fetchall()
    assert stale_statuses == [("stale",), ("current",)]


def test_ut_c2_05_deletion_and_stale_are_exclusive(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-05"""
    old_version = _write_source(
        tmp_path / "exports/demo-artifact-v1.md",
        {
            "source_kind": "document_export",
            "export_run_id": "RUN-1",
            "format": "md",
            "path": "exports/demo-artifact.md",
            "renderer": "pandoc",
            "byte_size": "10",
            "created_at": "2026-06-26T00:00:00Z",
            "evidence_path": "exports/demo-artifact-v1.md",
        },
        "version 1",
    )
    rebuild_projection(migrated_db, load_sources(tmp_path))
    assert migrated_db.execute("SELECT count(*) FROM document_export_artifacts").fetchone()[0] == 1

    old_version.unlink()
    rebuild_projection(migrated_db, load_sources(tmp_path))
    assert migrated_db.execute("SELECT count(*) FROM document_export_artifacts").fetchone()[0] == 0

    _write_source(
        tmp_path / "exports/demo-artifact-v2.md",
        {
            "source_kind": "document_export",
            "export_run_id": "RUN-2",
            "format": "md",
            "path": "exports/demo-artifact.md",
            "renderer": "pandoc",
            "byte_size": "10",
            "created_at": "2026-06-26T00:02:00Z",
            "evidence_path": "exports/demo-artifact-v2.md",
        },
        "version 2",
    )
    _write_source(
        tmp_path / "exports/demo-artifact-v3.md",
        {
            "source_kind": "document_export",
            "export_run_id": "RUN-3",
            "format": "md",
            "path": "exports/demo-artifact.md",
            "renderer": "pandoc",
            "byte_size": "10",
            "created_at": "2026-06-26T00:03:00Z",
            "evidence_path": "exports/demo-artifact-v3.md",
        },
        "version 3",
    )
    rebuild_projection(migrated_db, load_sources(tmp_path))

    statuses = migrated_db.execute(
        "SELECT stale_status FROM document_export_artifacts ORDER BY created_at"
    ).fetchall()
    assert statuses == [("stale",), ("current",)]


@pytest.mark.parametrize(
    ("row", "raises"),
    [
        ({"artifact_id": "artifact-1", "path": "docs/v3/engine/demo.md"}, False),
        ({"summary": "api_key=sk-live-1234567890abcdef"}, True),
        ({"summary": "User: hello\nAssistant: raw transcript"}, True),
        ({"summary": "owner email alice@example.com"}, True),
    ],
)
def test_ut_c2_06_assert_no_sensitive_payload_blocks_secrets_and_transcripts(
    row: dict[str, str],
    raises: bool,
) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-06"""
    table = TABLE_BY_NAME["artifact_registry"]
    if raises:
        with pytest.raises(SensitivePayloadError):
            assert_no_sensitive_payload(row, table)
    else:
        assert_no_sensitive_payload(row, table)


def test_ut_c2_07_append_event_is_idempotent_by_logical_key(migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-07"""
    event = {
        "table": "test_result_events",
        "ut_id": "UT-C2-07",
        "run_id": "RUN-7",
        "seq": "1",
        "status": "red",
        "run_at": "2026-06-26T00:00:00Z",
        "command": "pytest -q",
        "digest": "abc123",
    }
    append_event(migrated_db, event)
    event["status"] = "green"
    append_event(migrated_db, event)

    rows = _fetch_rows(migrated_db, "test_result_events", "ut_id, run_id, seq")
    assert len(rows) == 1
    assert rows[0][4] == "green"


def test_ut_c2_08_upsert_row_uses_on_conflict_and_stable_id(migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-08"""
    artifact_table = TABLE_BY_NAME["artifact_registry"]
    path = "docs/v3/engine/demo-artifact.md"
    row = {
        "path": path,
        "artifact_type": "design",
        "pair_artifact": "cli/lib/v3/tests/test_projection_writer.py",
        "status": "current",
        "updated_at": "2026-06-26T00:00:00Z",
    }
    artifact_id = upsert_row(migrated_db, artifact_table, row)
    row["status"] = "stale"
    upsert_row(migrated_db, artifact_table, row)

    rows = _fetch_rows(migrated_db, "artifact_registry", "artifact_id")
    assert len(rows) == 1
    assert artifact_id == stable_id("artifact_registry", path)
    assert rows[0][0] == stable_id("artifact_registry", path)
    assert rows[0][4] == "stale"


def test_ut_c2_09_unresolved_join_is_reported_to_findings(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-09"""
    _write_source(
        tmp_path / "docs/v3/engine/bad-trace.md",
        {
            "source_kind": "trace_edge",
            "from_artifact": "docs/v3/engine/missing-source.md",
            "to_artifact": "docs/v3/engine/missing-target.md",
            "edge_kind": "tests",
            "plan_id": "PLAN-MISSING",
            "status": "active",
        },
        "broken trace",
    )

    rebuild_projection(migrated_db, load_sources(tmp_path))

    findings = migrated_db.execute(
        "SELECT kind, severity, subject_id FROM findings ORDER BY finding_id"
    ).fetchall()
    assert ("unresolved-join", "warning", "docs/v3/engine/bad-trace.md") in findings


def test_ut_c2_10_rebuild_separates_fail_and_warn_findings(tmp_path: Path, migrated_db: sqlite3.Connection) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-10"""
    bad_frontmatter = tmp_path / "docs/v3/engine/bad-frontmatter.md"
    bad_frontmatter.parent.mkdir(parents=True, exist_ok=True)
    bad_frontmatter.write_text("---\nsource_kind plan\n---\nbody\n", encoding="utf-8")
    _write_source(
        tmp_path / "docs/plans/L7/bad-plan.md",
        {
            "source_kind": "plan",
            "kind": "impl",
            "layer": "L7",
            "drive": "be",
            "status": "draft",
            "updated_at": "2026-06-26T00:00:00Z",
        },
        "missing plan_id",
    )

    rebuild_projection(migrated_db, load_sources(tmp_path))

    statuses = migrated_db.execute(
        "SELECT status, subject_id FROM findings ORDER BY finding_id"
    ).fetchall()
    assert ("fail", "docs/v3/engine/bad-frontmatter.md") in statuses
    assert ("warn", "docs/plans/L7/bad-plan.md") in statuses


def test_ut_c2_11_sources_enumeration_uses_git_then_fallback_and_fail_closes_on_shrink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: L7-v3-engine-c2-projection-writerplan UT-C2-11"""
    kept = _write_source(
        tmp_path / "docs/plans/L7/kept.md",
        {"source_kind": "plan", "plan_id": "PLAN-KEPT", "kind": "impl", "layer": "L7", "drive": "be", "status": "draft", "updated_at": "2026-06-26T00:00:00Z"},
        "body",
    )
    missing = _write_source(
        tmp_path / "docs/plans/L7/missing.md",
        {"source_kind": "plan", "plan_id": "PLAN-MISSING", "kind": "impl", "layer": "L7", "drive": "be", "status": "draft", "updated_at": "2026-06-26T00:00:00Z"},
        "body",
    )

    from cli.lib.v3.projection import sources as sources_module

    def _git_failure(*_args: object, **_kwargs: object) -> object:
        raise OSError("git unavailable")

    monkeypatch.setattr(sources_module.subprocess, "run", _git_failure)
    names = {Path(path).name for path in enumerate_source_files(tmp_path)}
    assert names == {kept.name, missing.name}

    monkeypatch.setattr(
        sources_module,
        "_walk_source_files",
        lambda _root: [str(kept)],
    )
    with pytest.raises(SourceEnumerationError):
        enumerate_source_files(tmp_path)
