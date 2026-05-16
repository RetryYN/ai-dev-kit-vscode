import json
import os
import sqlite3
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


STOP_HOOK = REPO_ROOT / ".claude" / "hooks" / "stop.sh"
SESSION_START = REPO_ROOT / "cli" / "libexec" / "helix-session-start"


def _init_project(tmp_path: Path, name: str) -> tuple[Path, Path]:
    project_root = tmp_path / name
    db_path = project_root / ".helix" / "helix.db"
    with redirect_stdout(StringIO()):
        helix_db.init_db(str(db_path))
    return project_root, db_path


def _fetch_row(db_path: Path, session_id: str) -> sqlite3.Row | None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            """
            SELECT session_id, actor, related_plan_id, tool_uses_count, tokens_total, cost_usd,
                   started_at, ended_at, last_updated_at
            FROM session_telemetry
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
    finally:
        conn.close()


def _write_session_start_setup(tmp_path: Path, project_root: Path) -> dict[str, str]:
    home = tmp_path / "home"
    claude_dir = home / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "CLAUDE.md").write_text(
        "@~/ai-dev-kit-vscode/skills/SKILL_MAP.md\n",
        encoding="utf-8",
    )
    (claude_dir / "settings.json").write_text(
        json.dumps({"hooks": {"SessionStart": [{"command": "helix-session-start"}]}}),
        encoding="utf-8",
    )
    (home / ".bashrc").write_text(
        "export PATH=$PATH:~/ai-dev-kit-vscode/cli\n",
        encoding="utf-8",
    )
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(project_root),
            "HELIX_SKILL_SEARCH": "0",
            "TMPDIR": str(tmp_dir),
        }
    )
    return env


def test_upsert_session_telemetry_inserts_start_row(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "helper-insert")

    with helix_db._write_connection(str(db_path)) as conn:
        telemetry_id = helix_db.upsert_session_telemetry(
            conn,
            "sess-start",
            actor="claude-code",
            related_plan_id="PLAN-072",
        )

    row = _fetch_row(db_path, "sess-start")

    assert telemetry_id > 0
    assert row is not None
    assert row["actor"] == "claude-code"
    assert row["related_plan_id"] == "PLAN-072"
    assert row["tool_uses_count"] == 0
    assert row["tokens_total"] == 0
    assert row["cost_usd"] == pytest.approx(0.0)
    assert row["ended_at"] is None


def test_upsert_session_telemetry_updates_existing_row_on_end(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "helper-update")

    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.upsert_session_telemetry(conn, "sess-stop", actor="claude-code")
        helix_db.upsert_session_telemetry(
            conn,
            "sess-stop",
            actor="stop.sh",
            tool_uses_count=4,
            tokens_total=1200,
            cost_usd=0.75,
            ended=True,
        )

    row = _fetch_row(db_path, "sess-stop")

    assert row is not None
    assert row["actor"] == "stop.sh"
    assert row["tool_uses_count"] == 4
    assert row["tokens_total"] == 1200
    assert row["cost_usd"] == pytest.approx(0.75)
    assert row["started_at"]
    assert row["ended_at"]
    assert row["last_updated_at"]


def test_upsert_session_telemetry_rejects_negative_cost(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "helper-negative")

    with helix_db._write_connection(str(db_path)) as conn:
        with pytest.raises(ValueError, match="cost_usd must be >= 0"):
            helix_db.upsert_session_telemetry(
                conn,
                "sess-negative",
                actor="stop.sh",
                cost_usd=-0.01,
            )


def test_session_start_inserts_session_telemetry_row(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "session-start")
    env = _write_session_start_setup(tmp_path, project_root)
    payload = json.dumps({"session_id": "stdin-session"})

    proc = subprocess.run(
        ["bash", str(SESSION_START)],
        cwd=project_root,
        env=env,
        input=payload,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )

    output = json.loads(proc.stdout)
    row = _fetch_row(db_path, "stdin-session")

    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert row is not None
    assert row["actor"] == "claude-code"
    assert row["tool_uses_count"] == 0
    assert row["tokens_total"] == 0
    assert row["cost_usd"] == pytest.approx(0.0)
    assert row["ended_at"] is None


def test_stop_hook_upserts_session_telemetry_from_stdin(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "stop-hook")

    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.upsert_session_telemetry(conn, "stop-stdin", actor="claude-code")

    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(project_root),
            "HELIX_SESSION_ID": "stop-stdin",
            "HELIX_TOOL_USES": "1",
            "HELIX_HOOK_DURATION_MS": "8",
        }
    )
    payload = json.dumps(
        {
            "session_id": "stop-stdin",
            "tool_uses": [{"tool": "Edit"}, {"tool": "Bash"}],
            "tokens": 4321,
            "cost": 1.25,
        }
    )

    proc = subprocess.run(
        [str(STOP_HOOK)],
        cwd=project_root,
        env=env,
        input=payload,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )

    row = _fetch_row(db_path, "stop-stdin")

    assert proc.returncode == 0
    assert row is not None
    assert row["actor"] == "stop.sh"
    assert row["tool_uses_count"] == 2
    assert row["tokens_total"] == 4321
    assert row["cost_usd"] == pytest.approx(1.25)
    assert row["ended_at"] is not None


def test_stop_hook_warns_and_continues_on_invalid_stdin(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "stop-hook-invalid")
    env = os.environ.copy()
    env.update(
        {
            "HELIX_HOME": str(REPO_ROOT),
            "HELIX_PROJECT_ROOT": str(project_root),
        }
    )

    proc = subprocess.run(
        [str(STOP_HOOK)],
        cwd=project_root,
        env=env,
        input="{not-json",
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    conn = sqlite3.connect(str(db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM session_telemetry").fetchone()[0]
    finally:
        conn.close()

    assert proc.returncode == 0
    assert "WARNING: stop hook telemetry skipped: stdin is not valid JSON" in proc.stderr
    assert count == 0
