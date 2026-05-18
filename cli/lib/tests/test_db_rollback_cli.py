"""PLAN-086 rollback CLI tests.

DoD 検証: PLAN-086-rollback-fault-injection-drill.md T1-T5
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CLI = REPO_ROOT / "cli" / "helix"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


def _prepare_project(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    project = tmp_path / "project"
    helix_dir = project / ".helix"
    helix_dir.mkdir(parents=True)
    home = tmp_path / "home"
    home.mkdir()
    shutil.copy2(REPO_ROOT / "cli/templates/phase.yaml", helix_dir / "phase.yaml")
    shutil.copy2(REPO_ROOT / "cli/templates/gate-checks.yaml", helix_dir / "gate-checks.yaml")
    shutil.copy2(REPO_ROOT / "cli/templates/doc-map.yaml", helix_dir / "doc-map.yaml")
    (helix_dir / "matrix.yaml").write_text("deliverables: []\n", encoding="utf-8")
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    env["HOME"] = str(home)
    env["HELIX_DB_ROLLBACK_SKIP_DOCTOR"] = "1"
    return project, env


def _create_schema_db(path: Path, version: int) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
            (version, "2026-05-19T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()


def _create_event_db(path: Path, rows: int) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_envelope (
                event_id TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                db_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (db_name, event_id)
            )
            """
        )
        for idx in range(rows):
            conn.execute(
                """
                INSERT INTO event_envelope(
                    event_id, aggregate_id, aggregate_type, db_name, event_type, payload, correlation_id, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"00000000-0000-7000-8000-0000000000{idx:02d}",
                    f"agg-{idx}",
                    "phase",
                    path.stem,
                    "phase.transitioned",
                    json.dumps({"from_phase": "L3", "to_phase": "L4", "owner": "codex"}),
                    f"10000000-0000-7000-8000-0000000000{idx:02d}",
                    "2026-05-19T00:00:00+00:00",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _seed_fixture(project: Path) -> Path:
    helix_dir = project / ".helix"
    backups_dir = helix_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    current_db = helix_dir / "helix.db"
    backup_db = backups_dir / "2026-05-19T00-00-00_pre_v31.db"

    _create_schema_db(current_db, 32)
    _create_schema_db(backup_db, 30)
    _create_event_db(helix_dir / "orchestration.db", 2)
    _create_event_db(helix_dir / "vmodel.db", 1)
    _create_event_db(helix_dir / "scrum.db", 0)
    for name in ("plan.db", "backend.db", "frontend.db"):
        _create_schema_db(helix_dir / name, 31)
    return backup_db


def _run_cli(project: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), "db", *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_shows_dev_only_warning(tmp_path: Path) -> None:
    """DoD 検証: PLAN-086-rollback-fault-injection-drill.md T1"""
    project, env = _prepare_project(tmp_path)

    result = _run_cli(project, env, "rollback", "--help")

    assert result.returncode == 0
    assert result.stdout.startswith("WARNING: This is a dev-only convenience tool")
    assert "forward-only undo migration" in result.stdout


def test_dry_run_prints_preflight_and_plan(tmp_path: Path) -> None:
    """DoD 検証: PLAN-086-rollback-fault-injection-drill.md T2"""
    project, env = _prepare_project(tmp_path)
    backup_db = _seed_fixture(project)

    result = _run_cli(
        project,
        env,
        "rollback",
        "--to",
        "v30",
        "--backup-path",
        str(backup_db),
    )

    assert result.returncode == 0, result.stderr
    assert "mode: dry-run" in result.stdout
    assert "preflight: PASS" in result.stdout
    assert "diff_event_count: 3" in result.stdout
    assert "next_step: rerun with --confirm" in result.stdout


def test_confirm_restores_backup_and_archives_split_dbs(tmp_path: Path) -> None:
    """DoD 検証: PLAN-086-rollback-fault-injection-drill.md T3"""
    project, env = _prepare_project(tmp_path)
    backup_db = _seed_fixture(project)

    result = _run_cli(
        project,
        env,
        "rollback",
        "--to",
        "v30",
        "--backup-path",
        str(backup_db),
        "--confirm",
    )

    helix_dir = project / ".helix"
    assert result.returncode == 0, result.stderr
    archive_roots = sorted((helix_dir / "v31-archive").iterdir())
    assert "rollback: completed" in result.stdout
    with sqlite3.connect(str(helix_dir / "helix.db")) as conn:
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 30
    assert (helix_dir / "helix.db.pre-rollback.bak").exists()
    assert len(archive_roots) == 1
    archived_names = {path.name for path in archive_roots[0].iterdir()}
    assert archived_names == {
        "orchestration.db",
        "vmodel.db",
        "scrum.db",
        "plan.db",
        "backend.db",
        "frontend.db",
    }


def test_preflight_fails_when_backup_is_missing(tmp_path: Path) -> None:
    """DoD 検証: PLAN-086-rollback-fault-injection-drill.md T4"""
    project, env = _prepare_project(tmp_path)
    helix_dir = project / ".helix"
    _create_schema_db(helix_dir / "helix.db", 32)

    result = _run_cli(
        project,
        env,
        "rollback",
        "--to",
        "v30",
        "--backup-path",
        str(helix_dir / "backups" / "missing_pre_v31.db"),
    )

    assert result.returncode == 1
    assert "preflight: FAIL" in result.stdout
    assert "backup file が存在しません" in result.stdout


def test_export_diff_writes_json_dump(tmp_path: Path) -> None:
    """DoD 検証: PLAN-086-rollback-fault-injection-drill.md T5"""
    project, env = _prepare_project(tmp_path)
    backup_db = _seed_fixture(project)
    export_path = project / "rollback-diff.json"

    result = _run_cli(
        project,
        env,
        "rollback",
        "--to",
        "v30",
        "--backup-path",
        str(backup_db),
        "--confirm",
        "--export-diff",
        str(export_path),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["total_event_count"] == 3
    assert {entry["db_name"] for entry in payload["databases"]} == {"orchestration", "vmodel", "scrum"}
    assert all("CREATE TABLE event_envelope" in entry["dump_sql"] for entry in payload["databases"])
