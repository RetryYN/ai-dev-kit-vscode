from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from migrations import v31_db_separation, v32_design_doc_web_search_audit, v33_gate_audit_metrics


HELIX_ROOT = Path(__file__).resolve().parents[3]


def _write_gate_checks(project_root: Path) -> None:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True, exist_ok=True)
    (helix_dir / "gate-checks.yaml").write_text(
        "G2:\n"
        "  name: G2 design doc audit\n"
        "  static:\n"
        "  ai:\n"
        "G3:\n"
        "  name: G3 design doc audit\n"
        "  static:\n"
        "  ai:\n",
        encoding="utf-8",
    )


def _write_phase(project_root: Path) -> None:
    (project_root / ".helix" / "phase.yaml").write_text(
        "current_phase: L4\n"
        "sprint:\n"
        "  drive: be\n"
        "  ui: false\n"
        "gates:\n"
        "  G1:\n"
        "    status: passed\n"
        "  G2:\n"
        "    status: passed\n",
        encoding="utf-8",
    )


def _init_project(tmp_path: Path, *, plan_id: str, plan_body: str) -> Path:
    project_root = tmp_path / "project"
    (project_root / "docs" / "plans").mkdir(parents=True)
    _write_gate_checks(project_root)
    _write_phase(project_root)
    helix_db.init_db(str(project_root / ".helix" / "helix.db"))
    (project_root / "docs" / "plans" / f"{plan_id}-test.md").write_text(plan_body, encoding="utf-8")
    return project_root


def _run_gate(project_root: Path, gate: str, *, plan_id: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {
        "HOME": str(project_root / "home"),
        "HELIX_HOME": str(HELIX_ROOT),
        "HELIX_PROJECT_ROOT": str(project_root),
        "HELIX_DISABLE_FEEDBACK": "1",
        "HELIX_PLAN_ID": plan_id,
        "PATH": f"{HELIX_ROOT / 'cli'}:{Path('/usr/bin')}:{Path('/bin')}",
    }
    if extra_env:
        env.update(extra_env)
    (project_root / "home").mkdir(exist_ok=True)
    return subprocess.run(
        [
            str(HELIX_ROOT / "cli" / "helix-gate"),
            gate,
            "--static-only",
            "--readiness-mode",
            "skip",
        ],
        cwd=str(project_root),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _latest_gate_metric(project_root: Path) -> sqlite3.Row:
    conn = sqlite3.connect(str(project_root / ".helix" / "helix.db"))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT gate_name, plan_id, advisory_result, bypass_used
            FROM gate_audit_metrics
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def test_gate_design_doc_fail_close_blocks_without_references_for_g2_and_g3(tmp_path: Path) -> None:
    """DoD 検証: PLAN-089 Phase 2 S-001 (fail-close 有効時は G2/G3 とも未調査 plan を block)"""
    for gate in ("G2", "G3"):
        project_root = _init_project(tmp_path / gate.lower(), plan_id="PLAN-321", plan_body="# PLAN-321\n")

        completed = _run_gate(
            project_root,
            gate,
            plan_id="PLAN-321",
            extra_env={"HELIX_GATE_DESIGN_DOC_FAIL_CLOSE": "1"},
        )

        output = completed.stdout + completed.stderr
        assert completed.returncode == 1
        assert "FAIL [design_doc_web_search_audit]" in output
        assert f"=== {gate} FAIL" in output

        metric = _latest_gate_metric(project_root)
        assert dict(metric) == {
            "gate_name": gate,
            "plan_id": "PLAN-321",
            "advisory_result": "warn",
            "bypass_used": 0,
        }


def test_gate_design_doc_fail_close_accepts_bypass_with_reason(tmp_path: Path) -> None:
    """DoD 検証: PLAN-089 Phase 2 S-002 (valid bypass env は G3 fail-close を通過させる)"""
    project_root = _init_project(tmp_path, plan_id="PLAN-322", plan_body="# PLAN-322\n")

    completed = _run_gate(
        project_root,
        "G3",
        plan_id="PLAN-322",
        extra_env={
            "HELIX_GATE_DESIGN_DOC_FAIL_CLOSE": "1",
            "HELIX_ALLOW_DESIGN_DOC_NO_WEB": "1",
            "HELIX_DESIGN_DOC_NO_WEB_REASON": "hotfix doc follow-up",
        },
    )

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0
    assert "PASS [design_doc_web_search_audit]" in output
    assert "bypass accepted" in output
    assert "=== G3 PASS ===" in output

    metric = _latest_gate_metric(project_root)
    assert dict(metric) == {
        "gate_name": "G3",
        "plan_id": "PLAN-322",
        "advisory_result": "warn",
        "bypass_used": 1,
    }


def test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references(tmp_path: Path) -> None:
    """DoD 検証: PLAN-089 Phase 2 S-003 (既存許可 plan は fail-close 有効でも G2 を通過する)"""
    plan_body = (
        "# PLAN-323\n\n"
        "## 業界 standard 参照\n\n"
        "| 参照 | source | 役割 |\n"
        "|---|---|---|\n"
        "| Required checks | https://docs.github.com/actions | web evidence |\n"
        "| Existing OSS | https://github.com/example/existing-oss | oss evidence |\n"
    )
    project_root = _init_project(tmp_path, plan_id="PLAN-323", plan_body=plan_body)

    completed = _run_gate(
        project_root,
        "G2",
        plan_id="PLAN-323",
        extra_env={"HELIX_GATE_DESIGN_DOC_FAIL_CLOSE": "1"},
    )

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0
    assert "PASS [design_doc_web_search_audit]" in output
    assert "=== G2 PASS ===" in output

    metric = _latest_gate_metric(project_root)
    assert dict(metric) == {
        "gate_name": "G2",
        "plan_id": "PLAN-323",
        "advisory_result": "pass",
        "bypass_used": 0,
    }


def test_migrate_v32_to_v33_adds_gate_audit_metrics_and_records_schema_version(tmp_path: Path) -> None:
    """DoD 検証: PLAN-089 Phase 2 M-001 (v32→v33 で gate_audit_metrics と version 33 が入る)"""
    db_path = tmp_path / "legacy-v30.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(helix_db.SCHEMA)
    conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
    conn.execute("DELETE FROM schema_version")
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (30, '2026-05-19T00:00:00+00:00')"
    )
    conn.commit()

    try:
        v31_db_separation.migrate_v30_to_v31(conn)
        v32_design_doc_web_search_audit.migrate_v31_to_v32(conn)
        v33_gate_audit_metrics.migrate_v32_to_v33(conn)
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(gate_audit_metrics)").fetchall()]
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()]
    finally:
        conn.close()

    assert columns == [
        "id",
        "gate_name",
        "plan_id",
        "advisory_result",
        "bypass_used",
        "created_at",
    ]
    assert versions[-3:] == [31, 32, 33]
    assert helix_db.CURRENT_SCHEMA_VERSION == 33
