import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HELIX_PUSH = REPO_ROOT / "cli" / "helix-push"


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

    sys.path.insert(0, str(REPO_ROOT / "cli" / "lib"))
    import helix_db

    db_path = helix_dir / "helix.db"
    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.migrate(conn)

    return project_root


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
