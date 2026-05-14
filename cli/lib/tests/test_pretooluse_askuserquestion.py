import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "pretooluse-askuserquestion.sh"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_project(tmp_path: Path, name: str) -> tuple[Path, Path]:
    project_root = tmp_path / name
    db_path = project_root / ".helix" / "helix.db"
    with redirect_stdout(StringIO()):
        helix_db.init_db(str(db_path))
    return project_root, db_path


def _record_tl_advisor(db_path: Path, timestamp: str) -> None:
    with redirect_stdout(StringIO()):
        helix_db.record_invocation(str(db_path), {"timestamp": timestamp, "type": "codex", "role": "tl-advisor"})


def _run_hook(project_root: Path, payload: dict, now: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_root)
    if now is not None:
        env["HELIX_ASKUSERQUESTION_NOW"] = now
    return subprocess.run(
        [str(HOOK_PATH)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_hook_returns_0_for_non_askquestion_tool(tmp_path: Path) -> None:
    project_root, _ = _init_project(tmp_path, "non-ask")
    proc = _run_hook(project_root, {"tool_name": "Read", "tool_input": {"file_path": "README.md"}})

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_hook_warns_when_no_recent_tl_advisor(tmp_path: Path) -> None:
    project_root, _ = _init_project(tmp_path, "warn")
    proc = _run_hook(project_root, {"tool_name": "AskUserQuestion", "tool_input": {"questions": []}})

    assert proc.returncode == 0
    assert "tl-advisor" in proc.stderr
    assert "systemMessage" in proc.stdout


def test_hook_passes_when_recent_tl_advisor_invocation(tmp_path: Path) -> None:
    now = "2026-05-15T12:05:00"
    project_root, db_path = _init_project(tmp_path, "pass")
    _record_tl_advisor(db_path, "2026-05-15T12:04:00")

    proc = _run_hook(project_root, {"tool_name": "AskUserQuestion", "tool_input": {"questions": []}}, now=now)

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_hook_5min_window(tmp_path: Path) -> None:
    base_now = datetime.fromisoformat("2026-05-15T12:05:00")
    stale_root, stale_db = _init_project(tmp_path, "stale")
    _record_tl_advisor(stale_db, (base_now - timedelta(minutes=5, seconds=1)).isoformat())
    stale = _run_hook(stale_root, {"tool_name": "AskUserQuestion", "tool_input": {"questions": []}}, now=base_now.isoformat())

    fresh_root, fresh_db = _init_project(tmp_path, "fresh")
    _record_tl_advisor(fresh_db, (base_now - timedelta(minutes=4, seconds=59)).isoformat())
    fresh = _run_hook(fresh_root, {"tool_name": "AskUserQuestion", "tool_input": {"questions": []}}, now=base_now.isoformat())

    assert "tl-advisor" in stale.stderr
    assert stale.stdout != ""
    assert fresh.stdout == ""
    assert fresh.stderr == ""
