"""DoD 検証: PLAN-092-unit-test-design.md U-092-001〜005

PLAN-092 Sprint .1a の frontmatter parse / v35 upsert を固定する。
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from migrations import v35_plan_registry
import plan_parser


def _now_string() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_markdown(path: Path, frontmatter_text: str, body: str = "# Body\n") -> Path:
    path.write_text(f"---\n{frontmatter_text}\n---\n\n{body}", encoding="utf-8")
    return path


def _frontmatter_text(*, include_required: bool = True) -> str:
    plan_id_line = "plan_id: PLAN-092\n" if include_required else ""
    kind_line = "kind: impl\n" if include_required else ""
    layer_line = "layer: L4\n" if include_required else ""
    created_at = _now_string()
    revised_at = _now_string()
    return (
        f"{plan_id_line}"
        "title: PLAN-092 sample\n"
        f"{kind_line}"
        f"{layer_line}"
        "drive: be\n"
        "status: draft\n"
        "size: M\n"
        "owner: SE\n"
        f"created: \"{created_at}\"\n"
        f"revised: \"{revised_at}\"\n"
        "dependencies:\n"
        "  requires:\n"
        "    - PLAN-091\n"
        "  parent: PLAN-MM-001\n"
        "agent_slots:\n"
        "  - role: se\n"
        "    slot_label: SE primary\n"
        "  - role: qa\n"
        "    slot_label: QA validation\n"
        "related_docs:\n"
        "  - docs/plans/PLAN-091-v5-framework-core.md\n"
        "  - cli/ROLE_MAP.md\n"
        "generates:\n"
        "  - artifact_path: cli/lib/plan_parser.py\n"
        "    artifact_type: python_module\n"
        "  - artifact_path: cli/lib/tests/test_plan_parser.py\n"
        "    artifact_type: test\n"
        "test_design_ref: docs/v2/L4-test-design/PLAN-092-unit-test-design.md\n"
    )


def _sample_frontmatter(*, status: str = "draft") -> dict:
    timestamp = _now_string()
    return {
        "plan_id": "PLAN-092",
        "title": "PLAN-092 sample",
        "kind": "impl",
        "layer": "L4",
        "drive": "be",
        "status": status,
        "size": "M",
        "owner": "SE",
        "created": timestamp,
        "revised": _now_string(),
        "related_adr": ["ADR-026-posttooluse-plan-auto-register-decision"],
        "dependencies": {
            "requires": ["PLAN-091", "PLAN-090"],
            "parent": "PLAN-MM-001",
            "blocks": ["PLAN-093"],
        },
        "agent_slots": [
            {"role": "se", "slot_label": "SE primary"},
            {"role": "qa", "slot_label": "QA validation"},
        ],
        "related_docs": [
            "docs/plans/PLAN-091-v5-framework-core.md",
            "cli/ROLE_MAP.md",
        ],
        "generates": [
            {"artifact_path": "cli/lib/plan_parser.py", "artifact_type": "python_module"},
            {"artifact_path": "cli/lib/migrations/v35_plan_registry.py", "artifact_type": "python_module"},
        ],
        "test_design_ref": "docs/v2/L4-test-design/PLAN-092-unit-test-design.md",
    }


def _connect_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    v35_plan_registry.migrate_v34_to_v35(conn)
    return conn


def test_parse_frontmatter_populates_all_supported_fields(tmp_path: Path, capsys) -> None:
    path = _write_markdown(tmp_path / "PLAN-092-sample.md", _frontmatter_text())

    result = plan_parser.parse_frontmatter(str(path))
    captured = capsys.readouterr()

    assert result is not None
    assert result["plan_id"] == "PLAN-092"
    assert result["kind"] == "impl"
    assert result["layer"] == "L4"
    assert result["dependencies"]["requires"] == ["PLAN-091"]
    assert result["dependencies"]["parent"] == "PLAN-MM-001"
    assert len(result["agent_slots"]) == 2
    assert len(result["related_docs"]) == 2
    assert len(result["generates"]) == 2
    assert captured.err == ""


def test_parse_frontmatter_returns_none_and_warns_for_missing_or_invalid_frontmatter(
    tmp_path: Path, capsys
) -> None:
    non_target = tmp_path / "notes.md"
    no_frontmatter = tmp_path / "PLAN-092-no-frontmatter.md"
    non_target.write_text("# note\n", encoding="utf-8")
    no_frontmatter.write_text("# no frontmatter\n", encoding="utf-8")
    invalid_yaml = _write_markdown(
        tmp_path / "PLAN-092-invalid.md",
        "plan_id: PLAN-092\nagent_slots: [invalid",
    )

    result_non_target = plan_parser.parse_frontmatter(str(non_target))
    result_no_frontmatter = plan_parser.parse_frontmatter(str(no_frontmatter))
    result_invalid_yaml = plan_parser.parse_frontmatter(str(invalid_yaml))
    captured = capsys.readouterr()

    assert result_non_target == {}
    assert result_no_frontmatter is None
    assert result_invalid_yaml is None
    assert "WARNING" in captured.err
    assert "frontmatter" in captured.err.lower() or "parse" in captured.err.lower()
    assert "notes.md" not in captured.err


def test_parse_frontmatter_keeps_soft_warning_for_missing_required_fields(
    tmp_path: Path, capsys
) -> None:
    path = _write_markdown(
        tmp_path / "PLAN-092-missing-required.md",
        _frontmatter_text(include_required=False),
    )

    result = plan_parser.parse_frontmatter(str(path))
    captured = capsys.readouterr()

    assert result is not None
    assert "title" in result
    assert "plan_id" not in result
    assert "_warnings" in result
    assert any("plan_id" in warning for warning in result["_warnings"])
    assert any("kind" in warning for warning in result["_warnings"])
    assert any("layer" in warning for warning in result["_warnings"])
    assert "missing required fields" in captured.err


def test_upsert_plan_inserts_registry_and_related_tables() -> None:
    conn = _connect_memory_db()
    frontmatter = _sample_frontmatter()

    try:
        result = plan_parser.upsert_plan(conn, frontmatter, "docs/plans/PLAN-092-sample.md")
        registry_row = conn.execute(
            "SELECT * FROM plan_registry WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()
        dependency_count = conn.execute(
            "SELECT COUNT(*) FROM plan_dependencies WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()[0]
        slot_count = conn.execute(
            "SELECT COUNT(*) FROM plan_agent_slots WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()[0]
        reference_count = conn.execute(
            "SELECT COUNT(*) FROM plan_references WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()[0]
        generate_count = conn.execute(
            "SELECT COUNT(*) FROM plan_generates WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()[0]
        failure_log_count = conn.execute("SELECT COUNT(*) FROM failure_log").fetchone()[0]
        schema_versions = [
            row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()
        ]
        created_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert result["plan_id"] == "PLAN-092"
    assert result["counts"]["dependencies"] == 4
    assert result["counts"]["agent_slots"] == 2
    assert result["counts"]["references"] == 3
    assert result["counts"]["generates"] == 2
    assert json.loads(registry_row["frontmatter_json"])["plan_id"] == "PLAN-092"
    assert dependency_count == 4
    assert slot_count == 2
    assert reference_count == 3
    assert generate_count == 2
    assert failure_log_count == 0
    assert 35 in schema_versions
    assert set(v35_plan_registry.V35_TABLE_NAMES) <= created_tables


def test_upsert_plan_updates_registry_and_replaces_related_rows() -> None:
    conn = _connect_memory_db()
    initial = _sample_frontmatter(status="draft")
    updated = _sample_frontmatter(status="active")
    updated["dependencies"] = {
        "requires": ["PLAN-091"],
        "parent": "PLAN-MM-001",
        "blocks": ["PLAN-095"],
    }
    updated["agent_slots"] = [
        {"role": "se", "slot_label": "SE primary"},
        {"role": "experimental-role", "slot_label": "Experimental"},
    ]
    updated["related_docs"] = ["docs/plans/PLAN-093-plan-drift-detection-curator.md"]
    updated["generates"] = [
        {"artifact_path": "cli/lib/tests/test_plan_parser.py", "artifact_type": "test"},
    ]

    try:
        plan_parser.upsert_plan(conn, initial, "docs/plans/PLAN-092-sample.md")
        result = plan_parser.upsert_plan(conn, updated, "docs/plans/PLAN-092-sample.md")
        registry_row = conn.execute(
            "SELECT * FROM plan_registry WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()
        registry_count_for_plan = conn.execute(
            "SELECT COUNT(*) FROM plan_registry WHERE plan_id = ?",
            ("PLAN-092",),
        ).fetchone()[0]
        selected_dep_plan_ids = {
            row["dep_plan_id"]
            for row in conn.execute(
                "SELECT dep_plan_id FROM plan_dependencies WHERE plan_id = ?",
                ("PLAN-092",),
            ).fetchall()
        }
        selected_roles = {
            row["role"]
            for row in conn.execute(
                "SELECT role FROM plan_agent_slots WHERE plan_id = ?",
                ("PLAN-092",),
            ).fetchall()
        }
        selected_artifact_paths = {
            row["artifact_path"]
            for row in conn.execute(
                "SELECT artifact_path FROM plan_generates WHERE plan_id = ?",
                ("PLAN-092",),
            ).fetchall()
        }
    finally:
        conn.close()

    assert registry_count_for_plan == 1
    assert result["plan_id"] == "PLAN-092"
    assert result["status"] == "active"
    assert json.loads(registry_row["frontmatter_json"]) == updated
    assert registry_row["status"] == "active"
    assert "PLAN-090" not in selected_dep_plan_ids
    assert "PLAN-095" in selected_dep_plan_ids
    assert "experimental-role" in selected_roles
    assert "cli/lib/tests/test_plan_parser.py" in selected_artifact_paths
    assert "cli/lib/migrations/v35_plan_registry.py" not in selected_artifact_paths
