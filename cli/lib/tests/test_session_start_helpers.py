import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import session_start_helpers

HELIX_ROOT = LIB_DIR.parents[1]
SESSION_START = HELIX_ROOT / "cli" / "libexec" / "helix-session-start"
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def write_phase(
    project_root: Path,
    *,
    phase: str = "L3",
    mode: str = "forward",
    step: str | None = ".2",
    status: str = "active",
    drive: str | None = "be",
) -> None:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True)
    step_value = "null" if step is None else step
    drive_value = "null" if drive is None else drive
    (helix_dir / "phase.yaml").write_text(
        "\n".join(
            [
                f"current_phase: {phase}",
                f"current_mode: {mode}",
                "sprint:",
                f"  current_step: {step_value}",
                f"  status: {status}",
                f"  drive: {drive_value}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def fake_completed(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["helix"], returncode=0, stdout=stdout, stderr="")


def write_session_start_setup(tmp_path: Path, project_root: Path) -> dict[str, str]:
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
            "HELIX_HOME": str(HELIX_ROOT),
            "HELIX_PROJECT_ROOT": str(project_root),
            "HELIX_SKILL_SEARCH": "0",
            "TMPDIR": str(tmp_dir),
        }
    )
    return env


def init_sessions_db(project_root: Path) -> Path:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True)
    db_path = helix_dir / "helix.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cwd TEXT,
            claude_session_id TEXT,
            metadata TEXT
        );
        """
    )
    conn.close()
    return db_path


def run_session_start(project_root: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SESSION_START)],
        cwd=project_root,
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=True,
    )


def fetch_sessions(db_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            "SELECT id, cwd, claude_session_id FROM sessions ORDER BY started_at"
        ).fetchall()
    finally:
        conn.close()


def test_build_progress_block_no_helix(tmp_path: Path) -> None:
    assert session_start_helpers.build_progress_block(tmp_path) == ""


def test_helix_session_id_export_format(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = init_sessions_db(project_root)
    env = write_session_start_setup(tmp_path, project_root)

    completed = run_session_start(project_root, env)

    assert "export HELIX_SESSION_ID" in SESSION_START.read_text(encoding="utf-8")
    payload = json.loads(completed.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    rows = fetch_sessions(db_path)
    assert len(rows) == 1
    assert UUID_RE.fullmatch(rows[0]["id"])


def test_session_disabled_when_env_set(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = init_sessions_db(project_root)
    env = write_session_start_setup(tmp_path, project_root)
    env["HELIX_DISABLE_SESSIONS"] = "1"

    run_session_start(project_root, env)

    assert fetch_sessions(db_path) == []


def test_session_inserted_into_db(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    db_path = init_sessions_db(project_root)
    env = write_session_start_setup(tmp_path, project_root)
    env["CLAUDE_SESSION_ID"] = "claude-session-123"

    run_session_start(project_root, env)

    rows = fetch_sessions(db_path)
    assert len(rows) == 1
    assert rows[0]["cwd"] == str(project_root)
    assert rows[0]["claude_session_id"] == "claude-session-123"


def test_get_handover_task_returns_title_from_current_json(tmp_path: Path) -> None:
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir(parents=True)
    (handover_dir / "CURRENT.json").write_text(
        json.dumps({"task_title": "Sample Task"}),
        encoding="utf-8",
    )

    assert session_start_helpers.get_handover_task(tmp_path) == "Sample Task"


def test_get_handover_task_returns_empty_when_missing(tmp_path: Path) -> None:
    assert session_start_helpers.get_handover_task(tmp_path) == ""


def test_get_handover_task_returns_empty_on_malformed_json(tmp_path: Path) -> None:
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir(parents=True)
    (handover_dir / "CURRENT.json").write_text("{not-json", encoding="utf-8")

    assert session_start_helpers.get_handover_task(tmp_path) == ""


def test_build_progress_block_basic(tmp_path: Path) -> None:
    write_phase(tmp_path)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "## HELIX 現在の進捗" in block
    assert "Phase: L3 / Sprint: .2 / Mode: forward" in block
    assert "Drive: be" in block


def test_build_progress_block_includes_detect_dashboard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_phase(tmp_path)

    def fake_run(cmd, *args, **kwargs):
        if "detect" in cmd and "dashboard" in cmd:
            return fake_completed(
                "helix detect dashboard\n"
                "axis-00\ttelemetry baseline\t-\tblocked\n"
                "axis-01\tdead code drift\tG4\tfailed\n"
                "axis-14\torchestration integrity\tG6\tpassed\n"
            )
        return fake_completed("")

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "## HELIX Detect Dashboard" in block
    assert "axis-01\tdead code drift\tG4\tfailed" in block
    assert "axis-14\torchestration integrity\tG6\tpassed" in block
    assert "axis-00\ttelemetry baseline" not in block


def test_build_progress_block_with_interrupted(tmp_path: Path, monkeypatch) -> None:
    write_phase(tmp_path, status="interrupted")

    def fake_run(*args, **kwargs):
        payload = [{"id": "INT-001", "reason": "PC終了", "status": "open"}]
        return fake_completed(json.dumps(payload, ensure_ascii=False))

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "⚠️ 前回セッション中断中" in block
    assert "Interrupt ID: INT-001 (reason: PC終了)" in block
    assert "helix interrupt resume --id INT-001" in block


def test_build_progress_block_with_handover(tmp_path: Path, monkeypatch) -> None:
    write_phase(tmp_path)
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir()
    (handover_dir / "CURRENT.json").write_text("{}", encoding="utf-8")

    def fake_run(*args, **kwargs):
        payload = {
            "exists": True,
            "owner": "codex",
            "task": {"id": "T-001", "title": "JWT 実装", "status": "ready_for_review"},
        }
        return fake_completed(json.dumps(payload, ensure_ascii=False))

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "🤝 Handover 引き継ぎ中" in block
    assert 'Task: T-001 "JWT 実装" (owner=codex, status=ready_for_review)' in block
    assert "helix handover resume" in block


def test_build_progress_block_all_states(tmp_path: Path, monkeypatch) -> None:
    write_phase(tmp_path, status="interrupted")
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir()
    (handover_dir / "CURRENT.json").write_text("{}", encoding="utf-8")

    def fake_run(cmd, *args, **kwargs):
        if "interrupt" in cmd:
            return fake_completed(
                json.dumps([{"id": "INT-001", "reason": "test", "status": "open"}])
            )
        payload = {
            "exists": True,
            "owner": "opus",
            "task": {"id": "T-002", "title": "handover test", "status": "in_progress"},
        }
        return fake_completed(json.dumps(payload))

    monkeypatch.setattr(session_start_helpers.subprocess, "run", fake_run)

    block = session_start_helpers.build_progress_block(tmp_path)

    assert "⚠️ 前回セッション中断中" in block
    assert "🤝 Handover 引き継ぎ中" in block
    assert "helix handover status" in block


def test_build_progress_block_corrupt_yaml(tmp_path: Path) -> None:
    helix_dir = tmp_path / ".helix"
    helix_dir.mkdir()
    (helix_dir / "phase.yaml").write_text("current_phase L3\n", encoding="utf-8")

    assert session_start_helpers.build_progress_block(tmp_path) == ""
