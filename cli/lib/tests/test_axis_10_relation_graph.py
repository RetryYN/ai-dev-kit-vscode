from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from detectors.axis_10_relation_graph import Axis10RelationGraph


def _create_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE detector_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                axis_id TEXT NOT NULL,
                detector_name TEXT NOT NULL,
                phase_gate TEXT,
                verdict TEXT NOT NULL,
                findings_json TEXT NOT NULL,
                cost_ms INTEGER NOT NULL,
                raw_json TEXT NOT NULL,
                config_json TEXT NOT NULL,
                command TEXT NOT NULL,
                db_path TEXT NOT NULL
            );
            CREATE TABLE code_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_entry_id INTEGER NOT NULL,
                to_entry_id INTEGER,
                to_external_ref TEXT,
                edge_type TEXT NOT NULL,
                weight INTEGER DEFAULT 1,
                source_line INTEGER,
                raw_meta TEXT
            );
            CREATE TABLE contract_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                symbol_id TEXT,
                version TEXT,
                schema_hash TEXT,
                breaking_change_flag INTEGER DEFAULT 0,
                introduced_plan TEXT,
                raw_spec TEXT
            );
            """
        )
        conn.execute(
            """
            INSERT INTO detector_runs (
                recorded_at, axis_id, detector_name, phase_gate, verdict,
                findings_json, cost_ms, raw_json, config_json, command, db_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-05-13T00:00:00Z",
                "axis-01",
                "dead code drift",
                "G4",
                "failed",
                "[]",
                5,
                '{"entries_scanned":1}',
                "{}",
                "run",
                str(db_path),
            ),
        )
        conn.execute(
            """
            INSERT INTO code_edges (
                from_entry_id, to_entry_id, to_external_ref, edge_type, weight, source_line, raw_meta
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                101,
                None,
                "helper.call",
                "call",
                1,
                12,
                '{"source_path":"cli/lib/demo.py"}',
            ),
        )
        conn.execute(
            """
            INSERT INTO contract_entries (
                contract_type, source_path, symbol_id, version, schema_hash, raw_spec
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "cli-contract",
                "docs/features/demo/D-API/api.yaml",
                "docs.features.demo.D-API.api",
                "1.0.0",
                "hash-1",
                "{}",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_axis_10_relation_graph_aggregates_db_and_config_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    (project_root / "cli").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude").mkdir(parents=True, exist_ok=True)
    (project_root / "cli" / "helix-sample").write_text(
        "#!/bin/bash\n"
        "source ./lib/common.sh\n"
        "helper() {\n"
        "  :\n"
        "}\n"
        "main() {\n"
        "  helper\n"
        "}\n"
        "main\n",
        encoding="utf-8",
    )
    (project_root / ".claude" / "settings.json").write_text(
        (
            "{\n"
            '  "hooks": {\n'
            '    "PreToolUse": [\n'
            "      {\n"
            '        "matcher": "Bash",\n'
            '        "hooks": [{"type": "command", "command": "~/ai-dev-kit-vscode/cli/libexec/helix-pre-bash"}]\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n"
        ),
        encoding="utf-8",
    )
    db_path = project_root / ".helix" / "helix.db"
    _create_db(db_path)
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))

    result = Axis10RelationGraph().run(db_path)

    assert result.verdict == "passed"
    assert result.findings == []
    assert result.raw["detector_count"] == 1
    assert result.raw["code_edge_count"] == 1
    assert result.raw["contract_count"] == 1
    assert result.raw["bash_trace_count"] >= 2
    assert result.raw["hook_count"] == 1
    assert result.raw["node_count"] > 0
    assert result.raw["edge_count"] > 0
    assert "graph LR" in result.raw["mermaid"]
    assert "axis-01" in result.raw["mermaid"]
    assert "docs/features/demo/D-API/api.yaml" in result.raw["mermaid"]
    assert "cli/helix-sample" in result.raw["mermaid"]
    assert "helix-pre-bash" in result.raw["mermaid"]
