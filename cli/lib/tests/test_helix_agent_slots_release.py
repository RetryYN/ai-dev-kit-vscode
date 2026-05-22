"""CLI release helper tests for `helix agent slots`.

DoD 検証:
- `slots release-stale --dry-run` は対象を列挙しつつ release しない
- `slots release-stale` は stale slot を cancelled で一括 release する
- `slots release <id>` は個別 release を簡略書式で実行する
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from cli.lib import agent_slots, helix_db


REPO_ROOT = Path(__file__).resolve().parents[3]
CLI = REPO_ROOT / "cli" / "helix-agent"


@pytest.fixture
def agent_cli_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    project = tmp_path / "project"
    home = tmp_path / "home"
    db_path = project / ".helix" / "helix.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HELIX_HOME", str(REPO_ROOT))
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project))
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PYTHONPATH", str(REPO_ROOT))
    monkeypatch.chdir(project)

    helix_db.init_db(str(db_path))

    return {
        "project": project,
        "db_path": db_path,
        "env": os.environ.copy(),
    }


def _run_agent(agent_cli_env: dict[str, object], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), *args],
        cwd=agent_cli_env["project"],
        env=agent_cli_env["env"],
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_stale_slots(db_path: Path, count: int = 3) -> list[int]:
    slot_ids = [
        agent_slots.fire_slot(
            "codex",
            role="se",
            plan_id="PLAN-082",
            task_id=f"TASK-{index + 1:03d}",
            sprint=".4",
        )
        for index in range(count)
    ]
    fired_at = (datetime.now(UTC) - timedelta(minutes=6)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(str(db_path)) as conn:
        conn.executemany(
            "UPDATE agent_slots SET fired_at = ? WHERE id = ?",
            [(fired_at, slot_id) for slot_id in slot_ids],
        )
        conn.commit()
    return slot_ids


def _fetch_slot(db_path: Path, slot_id: int) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM agent_slots WHERE id = ?", (slot_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row


def test_slots_help_lists_release_commands(agent_cli_env: dict[str, object]) -> None:
    result = _run_agent(agent_cli_env, "slots", "--help")

    assert result.returncode == 0, result.stderr
    assert "helix agent slots release <slot_id>" in result.stdout
    assert "helix agent slots release-stale" in result.stdout


def test_release_stale_dry_run_lists_targets_without_releasing(agent_cli_env: dict[str, object]) -> None:
    db_path = agent_cli_env["db_path"]
    slot_ids = _seed_stale_slots(db_path)

    result = _run_agent(agent_cli_env, "slots", "release-stale", "--dry-run", "--json")
    payload = json.loads(result.stdout)

    assert result.returncode == 0, result.stderr
    assert payload["dry_run"] is True
    assert payload["found"] == 3
    assert payload["released"] == 0
    assert payload["failed"] == 0
    assert {row["id"] for row in payload["targets"]} == set(slot_ids)
    assert all(_fetch_slot(db_path, slot_id)["status"] == "running" for slot_id in slot_ids)
    assert all(_fetch_slot(db_path, slot_id)["released_at"] is None for slot_id in slot_ids)


def test_release_stale_releases_all_and_clears_stale_listing(agent_cli_env: dict[str, object]) -> None:
    db_path = agent_cli_env["db_path"]
    slot_ids = _seed_stale_slots(db_path)

    result = _run_agent(agent_cli_env, "slots", "release-stale", "--json")
    payload = json.loads(result.stdout)
    stale_after = _run_agent(agent_cli_env, "slots", "--stale", "--json")
    second_pass = _run_agent(agent_cli_env, "slots", "release-stale", "--json")
    second_payload = json.loads(second_pass.stdout)

    assert result.returncode == 0, result.stderr
    assert payload["found"] == 3
    assert payload["released"] == 3
    assert payload["failed"] == 0
    assert json.loads(stale_after.stdout) == []
    assert second_payload["found"] == 0
    assert second_payload["released"] == 0
    assert all(_fetch_slot(db_path, slot_id)["status"] == "cancelled" for slot_id in slot_ids)


def test_slots_release_releases_single_slot_with_status(agent_cli_env: dict[str, object]) -> None:
    db_path = agent_cli_env["db_path"]
    slot_id = agent_slots.fire_slot("codex", role="qa", plan_id="PLAN-082", task_id="TASK-900", sprint=".4")

    result = _run_agent(agent_cli_env, "slots", "release", str(slot_id), "--status", "completed")
    row = _fetch_slot(db_path, slot_id)

    assert result.returncode == 0, result.stderr
    assert f"released slot id={slot_id} (status=completed)" in result.stdout
    assert row["status"] == "completed"
    assert row["released_at"] is not None


def test_slots_release_rejects_unknown_slot_id(agent_cli_env: dict[str, object]) -> None:
    result = _run_agent(agent_cli_env, "slots", "release", "99999")

    assert result.returncode != 0
    assert "slot_id does not exist: 99999" in result.stderr


def test_slots_release_propagates_invalid_status(agent_cli_env: dict[str, object]) -> None:
    slot_id = agent_slots.fire_slot("codex", role="se", plan_id="PLAN-082", task_id="TASK-901", sprint=".4")

    result = _run_agent(agent_cli_env, "slots", "release", str(slot_id), "--status", "invalid_value")

    assert result.returncode != 0
    assert "invalid status: invalid_value" in result.stderr
