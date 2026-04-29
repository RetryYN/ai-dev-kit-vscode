import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import scheduler_helper as scheduler
import task_dispatcher


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "project" / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def _fetch_schedule(db_path: Path, schedule_id: str) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    finally:
        conn.close()


def test_parse_relative_schedule() -> None:
    assert scheduler.parse_schedule("+30s", 1000) == 1030
    assert scheduler.parse_schedule("+5m", 1000) == 1300
    assert scheduler.parse_schedule("+1h", 1000) == 4600
    assert scheduler.parse_schedule("+2d", 1000) == 173800


def test_parse_cron_every_five_minutes() -> None:
    base = 1_704_067_200  # 2024-01-01T00:00:00Z
    assert scheduler.parse_schedule("*/5 * * * *", base) == base + 300


def test_parse_cron_specific_hour_and_range() -> None:
    base = 1_704_067_200  # 2024-01-01T00:00:00Z
    expected = 1_704_096_000  # 2024-01-01T08:00:00Z
    assert scheduler.parse_schedule("0 8 1-2 * 1", base) == expected


def test_parse_invalid_schedule_fails() -> None:
    with pytest.raises(ValueError):
        scheduler.parse_schedule("+0m", 1000)
    with pytest.raises(ValueError):
        scheduler.parse_schedule("*/0 * * * *", 1000)
    with pytest.raises(ValueError):
        scheduler.parse_schedule("* * *", 1000)


def test_add_list_status_and_cancel(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    schedule_id = scheduler.add_schedule(
        str(db_path),
        "+5m",
        "helix:command",
        "status",
        id="sched-1",
        now=1000,
    )
    rows = scheduler.list_schedules(str(db_path))
    assert schedule_id == "sched-1"
    assert len(rows) == 1
    assert rows[0]["next_run_at"] == 1300
    assert scheduler.get_schedule(str(db_path), "sched-1")["task_payload"] == "status"
    assert scheduler.cancel_schedule(str(db_path), "sched-1") is True
    assert scheduler.list_schedules(str(db_path), "cancelled")[0]["id"] == "sched-1"


def test_run_due_dry_run_does_not_mutate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    scheduler.add_schedule(
        str(db_path),
        "+30s",
        "helix:command",
        "status",
        id="dry",
        now=1000,
        next_run_at=1,
    )
    result = scheduler.run_due_schedules(str(db_path), dry_run=True)
    row = _fetch_schedule(db_path, "dry")
    assert result == [{"id": "dry", "dry_run": True, "would_run": True, "ok": None, "output": ""}]
    assert row["status"] == "pending"
    assert row["last_run_at"] is None


def test_run_due_executes_allowlisted_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    config = home / ".config" / "helix"
    config.mkdir(parents=True)
    script = tmp_path / "allowed.sh"
    marker = tmp_path / "ran.txt"
    script.write_text(f"#!/bin/sh\necho ran > {marker}\n", encoding="utf-8")
    script.chmod(0o755)
    (config / "automation-allowlist.yaml").write_text(
        f"shell_scripts:\n  - {script.resolve()}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(task_dispatcher, "ALLOWLIST_PATH", config / "automation-allowlist.yaml")
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    scheduler.add_schedule(
        str(db_path),
        "+30s",
        "shell:script",
        str(script),
        id="due",
        now=1000,
        next_run_at=1,
    )
    result = scheduler.run_due_schedules(str(db_path))
    row = _fetch_schedule(db_path, "due")
    assert result[0]["ok"] is True
    assert marker.read_text(encoding="utf-8").strip() == "ran"
    assert row["status"] == "pending"
    assert row["last_run_at"] is not None
    assert row["next_run_at"] > row["last_run_at"]


def test_run_due_fails_closed_when_not_allowlisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    (home / ".config" / "helix").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(task_dispatcher, "ALLOWLIST_PATH", home / ".config" / "helix" / "automation-allowlist.yaml")
    db_path = _init_db(tmp_path)
    capsys.readouterr()
    scheduler.add_schedule(
        str(db_path),
        "+30s",
        "shell:script",
        str(tmp_path / "not-allowed.sh"),
        id="blocked",
        now=1000,
        next_run_at=1,
    )
    result = scheduler.run_due_schedules(str(db_path))
    row = _fetch_schedule(db_path, "blocked")
    assert result[0]["ok"] is False
    assert row["status"] == "failed"
    assert "not allowlisted" in row["last_error"]


def test_cli_add_and_status(tmp_path: Path) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    (project / ".helix").mkdir(parents=True)
    home.mkdir()
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project)
    env["HOME"] = str(home)
    add = subprocess.run(
        [
            str(REPO_ROOT / "cli" / "helix-scheduler"),
            "add",
            "--schedule",
            "+5m",
            "--task-type",
            "helix:command",
            "--task-payload",
            "status",
            "--id",
            "cli-1",
        ],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert add.returncode == 0
    assert json.loads(add.stdout)["id"] == "cli-1"
    status = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-scheduler"), "status", "--id", "cli-1"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert status.returncode == 0
    assert json.loads(status.stdout)["id"] == "cli-1"
