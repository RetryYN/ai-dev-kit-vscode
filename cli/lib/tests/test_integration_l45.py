import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HELIX_PUSH = REPO_ROOT / "cli" / "helix-push"
HELIX = REPO_ROOT / "cli" / "helix"

sys.path.insert(0, str(REPO_ROOT / "cli" / "lib"))
import contract_registry
import doc_map_matcher
import helix_db
import verify_agent


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """temp project workspace を .helix/helix.db 付きで構築。"""
    project_root = tmp_path / "project"
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True)

    # phase.yaml 最低限
    (helix_dir / "phase.yaml").write_text(
        "project: test-project\n"
        "current_mode: forward\n"
        "current_phase: L4\n"
        "gates: {}\n"
        "sprint:\n"
        "  current_step: null\n"
        "  status: active\n"
        "  drive: be\n"
        "  tracks: null\n"
        "  phase: null\n"
        "  phase_b:\n"
        "    current_step: null\n"
        "    status: pending\n"
        "    steps:\n"
        "      .b1: { status: pending }\n"
        "  steps:\n"
        "    .1a: { status: pending }\n"
        "    .2: { status: pending }\n"
        "    .3: { status: pending }\n"
        "  ui: false\n"
        "reverse_gates: {}\n",
        encoding="utf-8",
    )

    db_path = helix_dir / "helix.db"
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)

    return project_root


def _integration_env(project_root: Path) -> dict[str, str]:
    db_path = project_root / ".helix" / "helix.db"
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(project_root),
            "HELIX_DB_PATH": str(db_path),
        }
    )
    return env


def _init_git_repo(project_root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "helix@example.test"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.name", "HELIX Test"], cwd=project_root, check=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# IT-IP-05
def test_helix_push_records_automation_run(temp_project: Path) -> None:
    """helix-push --gate 実行で automation_runs に 1 行 INSERT されることを検証。"""
    db_path = temp_project / ".helix" / "helix.db"
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(temp_project),
            "HELIX_DB_PATH": str(db_path),
        }
    )

    proc = subprocess.run(
        [str(HELIX_PUSH), "--gate"],
        env=env,
        cwd=str(temp_project),
        capture_output=True,
        text=True,
        timeout=120,
    )

    # gate fail (1) は許容、入力エラー (2+) は不可
    assert proc.returncode in (0, 1), f"unexpected exit={proc.returncode}: {proc.stderr}"

    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, run_kind, status, started_at, ended_at, summary "
            "FROM automation_runs ORDER BY id"
        ).fetchall()

    assert len(rows) >= 1, "automation_runs must have at least 1 row"
    row = rows[0]
    run_id, run_kind, status, started_at, ended_at, summary = row
    assert run_kind == "push"
    assert status in ("completed", "failed")
    assert started_at and ended_at
    assert started_at <= ended_at
    summary_obj = json.loads(summary or "{}")
    assert summary_obj.get("trigger_source") == "helix-push"


def test_automation_run_audit_log_fk(temp_project: Path) -> None:
    """audit_log 行が存在する場合、run_id が automation_runs.id を参照することを検証 (hook 実行は別 path で発火)。"""
    db_path = temp_project / ".helix" / "helix.db"
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(temp_project),
            "HELIX_DB_PATH": str(db_path),
        }
    )

    subprocess.run(
        [str(HELIX_PUSH), "--gate"],
        env=env,
        cwd=str(temp_project),
        capture_output=True,
        text=True,
        timeout=120,
    )

    with sqlite3.connect(str(db_path)) as conn:
        automation_ids = {r[0] for r in conn.execute("SELECT id FROM automation_runs").fetchall()}
        for row in conn.execute("SELECT run_id FROM audit_log WHERE run_id IS NOT NULL").fetchall():
            assert row[0] in automation_ids, "audit_log.run_id must reference automation_runs.id"


# IT-MOD-06
def test_it_mod_06_catalog_trace_indexes_align_across_code_entry_contract_and_doc_map(temp_project: Path) -> None:
    _init_git_repo(temp_project)
    _write(
        temp_project / "cli/lib/sample_catalog.py",
        "\n".join(
            [
                "# @helix:index id=sample.catalog-entry domain=cli/lib summary=sample catalog entry",
                "def sample_catalog_entry():",
                "    return 1",
                "",
            ]
        ),
    )
    _write(
        temp_project / "docs/features/demo/D-API/api.yaml",
        "\n".join(
            [
                'openapi: "cli-contract/1.0"',
                "info:",
                "  title: demo",
                '  version: "1.0.0"',
                "",
            ]
        ),
    )
    _write(
        temp_project / ".helix/doc-map.yaml",
        "\n".join(
            [
                "triggers:",
                '  - pattern: "docs/features/demo/D-API/*.yaml"',
                "    phase: L5",
                "    on_write: design_sync",
                "    design_ref: MOD-06",
                "",
            ]
        ),
    )

    env = _integration_env(temp_project)
    subprocess.run(["git", "add", "."], cwd=temp_project, check=True)
    build = subprocess.run(
        [str(HELIX), "code", "build"],
        cwd=temp_project,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr

    add_entry = subprocess.run(
        [str(HELIX), "entry", "add", "--id=trace.demo", "--axis=design", "--ref=docs/features/demo/D-API/api.yaml", "--lifecycle=initial"],
        cwd=temp_project,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert add_entry.returncode == 0, add_entry.stderr

    link = subprocess.run(
        [str(HELIX), "entry", "link", "trace.demo", "sample.catalog-entry", "--kind=covers"],
        cwd=temp_project,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert link.returncode == 0, link.stderr

    inserted = contract_registry.bulk_insert(
        temp_project / ".helix" / "helix.db",
        contract_registry.scan_d_api_yamls(temp_project),
    )
    assert inserted == 1
    matches = doc_map_matcher._matched_triggers(
        doc_map_matcher._parse_doc_map(temp_project / ".helix/doc-map.yaml"),
        "docs/features/demo/D-API/api.yaml",
    )

    with sqlite3.connect(str(temp_project / ".helix" / "helix.db")) as conn:
        code_row = conn.execute(
            "SELECT id, path FROM code_index WHERE id = 'sample.catalog-entry'"
        ).fetchone()
        entry_row = conn.execute(
            "SELECT id, ref FROM entries WHERE id = 'trace.demo'"
        ).fetchone()
        link_row = conn.execute(
            "SELECT from_id, to_id, kind FROM links WHERE from_id = 'trace.demo' AND to_id = 'sample.catalog-entry'"
        ).fetchone()
        contract_row = conn.execute(
            "SELECT symbol_id, source_path FROM contract_entries WHERE source_path = 'docs/features/demo/D-API/api.yaml'"
        ).fetchone()

    assert code_row == ("sample.catalog-entry", "cli/lib/sample_catalog.py")
    assert entry_row == ("trace.demo", "docs/features/demo/D-API/api.yaml")
    assert link_row == ("trace.demo", "sample.catalog-entry", "covers")
    assert contract_row == ("docs.features.demo.D-API.api", "docs/features/demo/D-API/api.yaml")
    assert matches[0]["design_ref"] == "MOD-06"


# IT-DB-03
def test_it_db_03_trace_catalog_relations_stay_joinable(temp_project: Path) -> None:
    db_path = temp_project / ".helix" / "helix.db"
    helix_db.insert_row(
        db_path,
        "entries",
        {
            "id": "trace.db03",
            "axis": "design",
            "stack": "contract",
            "lifecycle": "initial",
            "ref": "docs/features/demo/D-API/api.yaml",
        },
    )
    helix_db.insert_row(
        db_path,
        "code_index",
        {
            "id": "sample.catalog-entry",
            "domain": "cli/lib",
            "summary": "sample catalog entry",
            "path": "cli/lib/sample_catalog.py",
            "line_no": 1,
            "symbol_line": 2,
            "bucket": "coverage_eligible",
        },
    )
    helix_db.insert_row(
        db_path,
        "entries",
        {
            "id": "sample.catalog-entry",
            "axis": "code",
            "stack": "back",
            "lifecycle": "initial",
            "ref": "cli/lib/sample_catalog.py",
        },
    )
    helix_db.insert_row(
        db_path,
        "links",
        {
            "from_id": "trace.db03",
            "to_id": "sample.catalog-entry",
            "kind": "covers",
            "metadata": '{"it_id":"IT-DB-03"}',
        },
    )
    contract_registry.bulk_insert(
        db_path,
        [
            {
                "contract_type": "cli-contract",
                "source_path": "docs/features/demo/D-API/api.yaml",
                "symbol_id": "docs.features.demo.D-API.api",
                "version": "1.0.0",
                "schema_hash": "it-db-03-hash",
                "breaking_change_flag": 0,
                "introduced_plan": "PLAN-G8-INTEGRATION-EXECUTION-GATE",
                "raw_spec": '{"openapi":"cli-contract/1.0"}',
            }
        ],
    )

    with sqlite3.connect(str(db_path)) as conn:
        contract_id = conn.execute(
            "SELECT id FROM contract_entries WHERE schema_hash = 'it-db-03-hash'"
        ).fetchone()[0]
    helix_db.insert_row(
        db_path,
        "test_design_entries",
        {
            "id": 1,
            "plan_id": "PLAN-G8-INTEGRATION-EXECUTION-GATE",
            "acceptance_key": "trace_catalog_relations",
            "contract_id": contract_id,
            "test_level": "integration",
            "paired_design_level": "detailed",
            "pyramid_layer": "integration",
            "test_target": "trace catalog joinability",
            "expected_status": "green",
        },
    )

    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            """
            SELECT ci.id, e.id, l.kind, ce.symbol_id, tde.id
            FROM code_index ci
            JOIN links l ON l.to_id = ci.id
            JOIN entries e ON e.id = l.from_id
            JOIN test_design_entries tde ON tde.id = 1
            JOIN contract_entries ce ON ce.id = tde.contract_id
            WHERE ci.id = 'sample.catalog-entry'
            """
        ).fetchone()

    assert row == (
        "sample.catalog-entry",
        "trace.db03",
        "covers",
        "docs.features.demo.D-API.api",
        1,
    )


# IT-DB-05
def test_it_db_05_requirement_quality_trace_stays_consistent_via_verify_run(temp_project: Path) -> None:
    db_path = temp_project / ".helix" / "helix.db"
    helix_db.insert_row(
        db_path,
        "requirements",
        {
            "req_id": "FR-QUALITY-01",
            "title": "Quality trace",
            "description": "Requirement/impl/test/verify alignment",
            "acceptance_criteria": "joined",
            "feature": "g8",
            "status": "draft",
            "updated_at": "2026-06-19T00:00:00Z",
        },
    )
    helix_db.insert_row(
        db_path,
        "req_impl_map",
        {
            "req_id": "FR-QUALITY-01",
            "impl_path": "cli/lib/sample_catalog.py",
            "impl_type": "code",
            "verified": 1,
        },
    )
    helix_db.insert_row(
        db_path,
        "req_test_map",
        {
            "req_id": "FR-QUALITY-01",
            "acc_index": "AC-01",
            "test_path": "cli/lib/tests/test_integration_l45.py::test_it_db_05_requirement_quality_trace_stays_consistent_via_verify_run",
            "test_result": "green",
        },
    )

    saved = verify_agent.save_to_db(
        "harvest",
        {"req_id": "FR-QUALITY-01"},
        {
            "requirement_id": "FR-QUALITY-01",
            "impl_path": "cli/lib/sample_catalog.py",
            "test_path": "cli/lib/tests/test_integration_l45.py::test_it_db_05_requirement_quality_trace_stays_consistent_via_verify_run",
            "status": "green",
        },
        True,
        project_root=temp_project,
        db_path=db_path,
        plan_id="PLAN-G8-INTEGRATION-EXECUTION-GATE",
        created_by="it-db-05",
    )

    assert saved["persisted"] is True

    with sqlite3.connect(str(db_path)) as conn:
        requirement = conn.execute(
            "SELECT req_id FROM requirements WHERE req_id = 'FR-QUALITY-01'"
        ).fetchone()
        impl = conn.execute(
            "SELECT req_id, impl_path, verified FROM req_impl_map WHERE req_id = 'FR-QUALITY-01'"
        ).fetchone()
        test_map = conn.execute(
            "SELECT req_id, test_path, test_result FROM req_test_map WHERE req_id = 'FR-QUALITY-01'"
        ).fetchone()
        verify_run = conn.execute(
            "SELECT plan_id, output_summary, created_by FROM verify_runs WHERE run_id = ?",
            (saved["run_id"],),
        ).fetchone()

    assert requirement == ("FR-QUALITY-01",)
    assert impl == ("FR-QUALITY-01", "cli/lib/sample_catalog.py", 1)
    assert test_map == (
        "FR-QUALITY-01",
        "cli/lib/tests/test_integration_l45.py::test_it_db_05_requirement_quality_trace_stays_consistent_via_verify_run",
        "green",
    )
    assert verify_run[0] == "PLAN-G8-INTEGRATION-EXECUTION-GATE"
    assert verify_run[2] == "it-db-05"
    assert "FR-QUALITY-01" in verify_run[1]
