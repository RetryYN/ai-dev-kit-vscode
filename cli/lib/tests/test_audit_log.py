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
POST_TOOL_USE_HOOK = REPO_ROOT / ".claude" / "hooks" / "post-tool-use.sh"
PRETOOLUSE_OPUS_HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse-opus-repo-block.sh"
PRETOOLUSE_ASK_HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse-askuserquestion.sh"


def _init_project(tmp_path: Path, name: str) -> tuple[Path, Path]:
    project_root = tmp_path / name
    db_path = project_root / ".helix" / "helix.db"
    with redirect_stdout(StringIO()):
        helix_db.init_db(str(db_path))
    return project_root, db_path


def _query_rows(db_path: Path, query: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def _run_stop_like_hook(hook_path: Path, project_root: Path, **extra_env: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    env.update(extra_env)
    return subprocess.run(
        [str(hook_path)],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _run_pretooluse_hook(
    hook_path: Path,
    project_root: Path,
    payload: dict,
    **extra_env: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["CLAUDE_PROJECT_DIR"] = str(project_root)
    env.update(extra_env)
    return subprocess.run(
        [str(hook_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_insert_audit_log_inserts_row(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "helper")

    with helix_db._write_connection(str(db_path)) as conn:
        audit_id = helix_db.insert_audit_log(
            conn,
            audit_kind="hook_exec",
            actor="stop.sh",
            payload={"hook_name": "stop", "duration_ms": 12},
        )

    row = _query_rows(
        db_path,
        "SELECT id, audit_kind, actor, run_id, payload FROM audit_log WHERE id = ?",
        (audit_id,),
    )[0]

    assert audit_id == row["id"]
    assert row["audit_kind"] == "hook_exec"
    assert row["actor"] == "stop.sh"
    assert row["run_id"] is None
    assert json.loads(row["payload"]) == {"hook_name": "stop", "duration_ms": 12}


def test_insert_audit_log_rejects_invalid_kind(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "invalid-kind")

    with helix_db._write_connection(str(db_path)) as conn:
        with pytest.raises(ValueError):
            helix_db.insert_audit_log(conn, audit_kind="bad_kind", actor="stop.sh")


def test_insert_audit_log_accepts_valid_run_id_fk(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "valid-run-id")

    with helix_db._write_connection(str(db_path)) as conn:
        run_id = helix_db.insert_automation_run(conn, "helix-push", "push", {"plan_id": "PLAN-072"})
        audit_id = helix_db.insert_audit_log(
            conn,
            audit_kind="hook_exec",
            actor="stop.sh",
            run_id=run_id,
            payload={"hook_name": "stop"},
        )

    row = _query_rows(db_path, "SELECT run_id FROM audit_log WHERE id = ?", (audit_id,))[0]
    assert row["run_id"] == run_id


def test_insert_audit_log_rejects_unknown_run_id_fk(tmp_path: Path) -> None:
    _, db_path = _init_project(tmp_path, "invalid-run-id")

    with helix_db._write_connection(str(db_path)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            helix_db.insert_audit_log(
                conn,
                audit_kind="hook_exec",
                actor="stop.sh",
                run_id=999999,
                payload={"hook_name": "stop"},
            )


def test_stop_hook_records_hook_exec_with_automation_run_reference(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "stop-hook")
    with helix_db._write_connection(str(db_path)) as conn:
        run_id = helix_db.insert_automation_run(conn, "helix-push", "push", {"plan_id": "PLAN-072"})

    proc = _run_stop_like_hook(
        STOP_HOOK,
        project_root,
        HELIX_AUTOMATION_RUN_ID=str(run_id),
        HELIX_TOOL_USES="3",
        HELIX_HOOK_DURATION_MS="12",
    )

    assert proc.returncode == 0
    invocation_rows = _query_rows(db_path, "SELECT id FROM invocation_log")
    audit_rows = _query_rows(
        db_path,
        "SELECT audit_kind, actor, run_id, payload FROM audit_log ORDER BY id",
    )

    assert invocation_rows == []
    assert len(audit_rows) == 1
    payload = json.loads(audit_rows[0]["payload"])
    assert audit_rows[0]["audit_kind"] == "hook_exec"
    assert audit_rows[0]["actor"] == "stop.sh"
    assert audit_rows[0]["run_id"] == run_id
    assert payload["hook_name"] == "stop"
    assert payload["tool_uses"] == 3
    assert payload["duration_ms"] == 12


def test_post_tool_use_hook_records_hook_exec(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "post-tool-use-hook")
    with helix_db._write_connection(str(db_path)) as conn:
        run_id = helix_db.insert_automation_run(conn, "helix-push", "push", {"plan_id": "PLAN-072"})

    proc = _run_stop_like_hook(
        POST_TOOL_USE_HOOK,
        project_root,
        HELIX_AUTOMATION_RUN_ID=str(run_id),
        HELIX_TOOL_USES="4",
        HELIX_HOOK_DURATION_MS="9",
    )

    assert proc.returncode == 0
    invocation_rows = _query_rows(db_path, "SELECT id FROM invocation_log")
    audit_rows = _query_rows(db_path, "SELECT audit_kind, actor, run_id, payload FROM audit_log ORDER BY id")

    assert invocation_rows == []
    assert len(audit_rows) == 1
    payload = json.loads(audit_rows[0]["payload"])
    assert audit_rows[0]["audit_kind"] == "hook_exec"
    assert audit_rows[0]["actor"] == "post-tool-use.sh"
    assert audit_rows[0]["run_id"] == run_id
    assert payload["hook_name"] == "post-tool-use"
    assert payload["tool_uses"] == 4
    assert payload["duration_ms"] == 9


def test_pretooluse_opus_repo_block_records_hook_and_gate(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "opus-block")

    proc = _run_pretooluse_hook(
        PRETOOLUSE_OPUS_HOOK,
        project_root,
        {"tool_name": "Edit", "tool_input": {"file_path": str(REPO_ROOT / "cli" / "lib" / "budget.py")}},
    )

    assert proc.returncode == 2
    rows = _query_rows(db_path, "SELECT audit_kind, actor, payload FROM audit_log ORDER BY id")

    assert [row["audit_kind"] for row in rows] == ["hook_exec", "gate_eval"]
    gate_payload = json.loads(rows[1]["payload"])
    assert rows[0]["actor"] == "pretooluse-opus-repo-block.sh"
    assert gate_payload["gate_name"] == "opus_repo_edit_policy"
    assert gate_payload["verdict"] == "blocked"


def test_pretooluse_askuserquestion_records_gate_eval(tmp_path: Path) -> None:
    project_root, db_path = _init_project(tmp_path, "askuserquestion")

    proc = _run_pretooluse_hook(
        PRETOOLUSE_ASK_HOOK,
        project_root,
        {"tool_name": "AskUserQuestion", "tool_input": {"questions": []}},
    )

    assert proc.returncode == 0
    rows = _query_rows(db_path, "SELECT audit_kind, actor, payload FROM audit_log ORDER BY id")

    assert [row["audit_kind"] for row in rows] == ["hook_exec", "gate_eval"]
    gate_payload = json.loads(rows[1]["payload"])
    assert rows[0]["actor"] == "pretooluse-askuserquestion.sh"
    assert gate_payload["gate_name"] == "tl_advisor_recent_check"
    assert gate_payload["verdict"] == "warn"
