import os
from pathlib import Path
import subprocess
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
HELIX_BIN = REPO_ROOT / "cli" / "helix"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _seed_functional_entries(db_path: Path, drive: str, statuses: list[str]) -> None:
    conn = helix_db.get_connection(db_path)
    try:
        for idx, status in enumerate(statuses, start=1):
            conn.execute(
                """
                INSERT INTO design_sprint_entries (
                    plan_id, sprint_id, sprint_type, layer, drive, track, pair_status, freeze_gate, subgate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("PLAN-100", f"SPRINT-{idx}", "functional", "functional", drive, "shared", status, "G3", "functional_freeze"),
            )
        conn.commit()
    finally:
        conn.close()


def _query_status(db_path: Path, drive: str) -> dict:
    conn = helix_db.get_connection(db_path)
    try:
        return helix_db.query_functional_freeze_status(conn, "PLAN-100", drive)
    finally:
        conn.close()


def _init_cli_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".helix").mkdir(parents=True)
    (project / "home").mkdir()
    helix_db.init_db(str(project / ".helix" / "helix.db"))
    return project


def _run_subgate(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(project),
            "HELIX_DISABLE_FEEDBACK": "1",
            "HOME": str(project / "home"),
            "PATH": f"{REPO_ROOT / 'cli'}:/usr/bin:/bin",
        }
    )
    return subprocess.run(
        [str(HELIX_BIN), "gate", "G3", "--subgate", "functional_freeze", *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_phase_drive(project: Path, drive: str) -> None:
    (project / ".helix" / "phase.yaml").write_text(
        f"current_phase: L3\nsprint:\n  drive: {drive}\n",
        encoding="utf-8",
    )


def _write_plan_frontmatter(project: Path, drive: str) -> None:
    plan_dir = project / ".helix" / "plans"
    docs_dir = project / "docs" / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "PLAN-100.yaml").write_text(
        'id: PLAN-100\ntitle: "Sample Plan"\nstatus: draft\ncreated_at: "2026-05-15T00:00:00Z"\n'
        'source_file: "docs/plans/PLAN-100-sample.md"\nreferences: []\nartifacts: []\nfinalized_at: null\n'
        'review:\n  status: approve\n  reviewed_at: "2026-05-15T00:00:00Z"\n  review_file: null\n',
        encoding="utf-8",
    )
    (docs_dir / "PLAN-100-sample.md").write_text(
        f"---\nplan_id: PLAN-100\ntitle: Sample Plan\nstatus: draft\ncreated: 2026-05-15\ndrive: {drive}\n---\n\nbody\n",
        encoding="utf-8",
    )


def test_query_functional_freeze_status_returns_missing_when_empty(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)

    result = _query_status(db_path, "fe")

    assert result == {
        "plan_id": "PLAN-100",
        "drive": "fe",
        "functional_pair_count": 0,
        "paired_count": 0,
        "pending_count": 0,
        "failed_count": 0,
        "verdict": "missing",
    }


def test_query_functional_freeze_status_returns_passed_when_all_paired(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "fe", ["paired", "paired"])

    result = _query_status(db_path, "fe")

    assert result["functional_pair_count"] == 2
    assert result["paired_count"] == 2
    assert result["pending_count"] == 0
    assert result["failed_count"] == 0
    assert result["verdict"] == "passed"


def test_query_functional_freeze_status_returns_failed_when_pending(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "fe", ["paired", "pending", "design_only", "test_only"])

    result = _query_status(db_path, "fe")

    assert result["functional_pair_count"] == 4
    assert result["paired_count"] == 1
    assert result["pending_count"] == 3
    assert result["failed_count"] == 0
    assert result["verdict"] == "failed"


def test_query_functional_freeze_status_returns_failed_when_failed(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "fe", ["paired", "failed"])

    result = _query_status(db_path, "fe")

    assert result["functional_pair_count"] == 2
    assert result["paired_count"] == 1
    assert result["pending_count"] == 0
    assert result["failed_count"] == 1
    assert result["verdict"] == "failed"


def test_subgate_multi_drive_query_be_fe_db_sequential(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "be", ["paired"])
    _seed_functional_entries(db_path, "fe", ["paired", "pending"])
    _seed_functional_entries(db_path, "db", ["failed"])

    be_result = _query_status(db_path, "be")
    fe_result = _query_status(db_path, "fe")
    db_result = _query_status(db_path, "db")

    assert [
        (be_result["drive"], be_result["functional_pair_count"], be_result["paired_count"], be_result["verdict"]),
        (fe_result["drive"], fe_result["functional_pair_count"], fe_result["pending_count"], fe_result["verdict"]),
        (db_result["drive"], db_result["functional_pair_count"], db_result["failed_count"], db_result["verdict"]),
    ] == [
        ("be", 1, 1, "passed"),
        ("fe", 2, 1, "failed"),
        ("db", 1, 1, "failed"),
    ]


def test_subgate_drive_switch_via_v22_api(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    _seed_functional_entries(db_path, "be", ["paired"])

    new_entry_id = helix_db.switch_drive_for_sprint(
        str(db_path),
        plan_id="PLAN-100",
        sprint_type="functional",
        layer="functional",
        old_drive="be",
        new_drive="fe",
        reason="switch to frontend validation",
        status_on_switch="preserved",
    )

    conn = helix_db.get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, drive, pair_status, previous_drive, status_on_switch
            FROM design_sprint_entries
            WHERE plan_id = ?
            ORDER BY id
            """,
            ("PLAN-100",),
        ).fetchall()
        be_result = helix_db.query_functional_freeze_status(conn, "PLAN-100", "be")
        fe_result = helix_db.query_functional_freeze_status(conn, "PLAN-100", "fe")
    finally:
        conn.close()

    assert [
        (row["id"], row["drive"], row["previous_drive"], row["status_on_switch"], row["pair_status"])
        for row in rows
    ] == [
        (rows[0]["id"], "be", None, "preserved", "paired"),
        (new_entry_id, "fe", "be", None, "pending"),
    ]
    assert be_result["verdict"] == "passed"
    assert fe_result["pending_count"] == 1
    assert fe_result["verdict"] == "failed"


def test_subgate_resolves_drive_from_phase_yaml(tmp_path: Path) -> None:
    project = _init_cli_project(tmp_path)
    _write_phase_drive(project, "fe")
    _seed_functional_entries(project / ".helix" / "helix.db", "fe", ["paired"])

    proc = _run_subgate(project, "--plan-id", "PLAN-100")

    assert proc.returncode == 0, proc.stderr
    assert '"drive": "fe"' in proc.stdout
    assert "override" not in proc.stderr


def test_subgate_resolves_drive_from_plan_frontmatter(tmp_path: Path) -> None:
    project = _init_cli_project(tmp_path)
    _write_plan_frontmatter(project, "fullstack")
    _seed_functional_entries(project / ".helix" / "helix.db", "fullstack", ["paired"])

    proc = _run_subgate(project, "--plan-id", "PLAN-100")

    assert proc.returncode == 0, proc.stderr
    assert '"drive": "fullstack"' in proc.stdout


def test_subgate_fails_closed_when_drive_cannot_be_resolved(tmp_path: Path) -> None:
    project = _init_cli_project(tmp_path)

    proc = _run_subgate(project, "--plan-id", "PLAN-100")

    assert proc.returncode == 1
    assert "--drive を指定してください" in proc.stderr
