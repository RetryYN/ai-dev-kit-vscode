from __future__ import annotations

import sqlite3

from cli.lib.v3.detectors.core import analyze_doc_contract, doc_contract_messages, load_doc_contract_input
from cli.lib.v3.detectors.runner import Finding
from cli.lib.v3.projection.upsert import stable_id
from cli.lib.v3.schema.ddl import migrate


def _insert_artifact(conn: sqlite3.Connection, *, path: str, artifact_type: str) -> None:
    conn.execute(
        "INSERT INTO artifact_registry(artifact_id, artifact_type, path, pair_artifact, status, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (
            stable_id("artifact_registry", path),
            artifact_type,
            path,
            "",
            "active",
            "2026-06-27T00:00:00Z",
        ),
    )


def test_doc_contract_clean_design_doc_has_no_findings(tmp_path) -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    path = tmp_path / "design.md"
    path.write_text(
        "---\n"
        "layer: L6\nstatus: draft\npair_artifact: self\nsub_doc: functional-design\n"
        "next_pair_freeze: L7\nplan: docs/plans/PLAN-L7-01-sample.md\n"
        "---\n\n# Design\n",
        encoding="utf-8",
    )
    _insert_artifact(conn, path=str(path), artifact_type="design_doc")

    result = analyze_doc_contract(load_doc_contract_input(conn))

    assert result.ok is True
    assert doc_contract_messages(result) == []


def test_doc_contract_flags_missing_frontmatter(tmp_path) -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    path = tmp_path / "missing-frontmatter.md"
    path.write_text("# body only\n", encoding="utf-8")
    _insert_artifact(conn, path=str(path), artifact_type="design_doc")

    result = analyze_doc_contract(load_doc_contract_input(conn))

    assert result.ok is False
    [finding] = doc_contract_messages(result)
    assert finding.subject == str(path)
    assert "frontmatter missing: layer" in finding.missing


def test_doc_contract_flags_missing_plan_sections(tmp_path) -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    path = tmp_path / "plan-missing-section.md"
    path.write_text(
        "---\n"
        "plan_id: PLAN-L7-01-sample\nkind: impl\nlayer: L7\ndrive: be\nstatus: draft\n"
        "agent_slots: []\ngenerates: []\ndependencies: {requires: [], blocks: []}\nreview_evidence: {}\n"
        "---\n\n"
        "## §0 concept\n## §1 background\n## §2 scope\n## §3 steps\n"
        "## §4 dod\n## §5 evidence\n## §6 glossary\n",
        encoding="utf-8",
    )
    _insert_artifact(conn, path=str(path), artifact_type="plan")

    result = analyze_doc_contract(load_doc_contract_input(conn))

    assert result.ok is False
    assert doc_contract_messages(result) == [
        Finding(id="FN-DET-15", severity="hard", subject=str(path), missing=("missing section: §7",))
    ]


def test_doc_contract_flags_invalid_plan_id(tmp_path) -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    path = tmp_path / "plan-invalid-id.md"
    path.write_text(
        "---\n"
        "plan_id: L7-v3-engine-phase8\nkind: impl\nlayer: L7\ndrive: be\nstatus: draft\n"
        "agent_slots: []\ngenerates: []\ndependencies: {requires: [], blocks: []}\nreview_evidence: {}\n"
        "---\n\n"
        "## §0 concept\n## §1 background\n## §2 scope\n## §3 steps\n"
        "## §4 dod\n## §5 evidence\n## §6 glossary\n## §7 fr delta\n",
        encoding="utf-8",
    )
    _insert_artifact(conn, path=str(path), artifact_type="plan")

    result = analyze_doc_contract(load_doc_contract_input(conn))

    assert result.ok is False
    assert doc_contract_messages(result) == [
        Finding(
            id="FN-DET-15",
            severity="hard",
            subject=str(path),
            missing=("invalid plan_id: L7-v3-engine-phase8",),
        )
    ]


def test_doc_contract_is_ok_when_no_doc_artifacts_exist() -> None:
    conn = sqlite3.connect(":memory:")
    migrate(conn)

    result = analyze_doc_contract(load_doc_contract_input(conn))

    assert result.ok is True
    assert doc_contract_messages(result) == []
