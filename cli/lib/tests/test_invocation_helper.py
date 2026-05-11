import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
import invocation_helper as helper


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    return db_path


def test_build_payload_variants() -> None:
    payload = helper.build_payload("codex", "se", "gpt-5.4", "W-1c", "PLAN-063", ".1c", "120", "48", "2500", "passed", "9", "1.25")
    missing = helper.build_payload(None, "", 123, None, "", None, "bad", object(), "oops", None, "abc", "NaN")

    assert payload["type"] == "codex"
    assert payload["input_bytes"] == 120
    assert payload["duration_ms"] == 2500
    assert payload["raw_meta"] == {
        "role": "se",
        "model": "gpt-5.4",
        "task_id": "W-1c",
        "plan_id": "PLAN-063",
        "sprint": ".1c",
        "decision": "passed",
        "cost_cents": 1.25,
        "duration_ms": 2500,
    }
    assert missing["type"] == "unknown"
    assert missing["role"] is None
    assert missing["model"] == "123"
    assert missing["input_bytes"] is None
    assert missing["output_bytes"] is None
    assert missing["duration_ms"] is None
    assert missing["parent_invocation_id"] is None
    assert "type" not in payload["raw_meta"]
    assert "input_bytes" not in payload["raw_meta"]
    assert "output_bytes" not in payload["raw_meta"]
    assert "parent_invocation_id" not in payload["raw_meta"]


def test_emit_from_env_outputs_json_and_persists_row(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "HELIX_INVOCATION_DB_PATH": str(db_path),
            "HELIX_INVOCATION_TYPE": "codex",
            "HELIX_INVOCATION_ROLE": "se",
            "HELIX_INVOCATION_MODEL": "gpt-5.4",
            "HELIX_INVOCATION_TASK_ID": "W-1c",
            "HELIX_INVOCATION_PLAN_ID": "PLAN-063",
            "HELIX_INVOCATION_SPRINT": ".1c",
            "HELIX_INVOCATION_INPUT_BYTES": "120",
            "HELIX_INVOCATION_OUTPUT_BYTES": "48",
            "HELIX_INVOCATION_DURATION_MS": "2500",
            "HELIX_INVOCATION_DECISION": "passed",
            "HELIX_INVOCATION_PARENT_INVOCATION_ID": "9",
            "HELIX_INVOCATION_COST_CENTS": "1.25",
        }
    )
    proc = subprocess.run([sys.executable, str(LIB_DIR / "invocation_helper.py"), "emit-from-env"], cwd=str(REPO_ROOT), env=env, capture_output=True, text=True, check=False)

    assert proc.returncode == 0, proc.stderr
    emitted = json.loads(proc.stdout.strip())
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("SELECT type, role, plan_id, task_id FROM invocation_log ORDER BY id DESC LIMIT 1").fetchone()
    finally:
        conn.close()

    assert emitted["ok"] is True
    assert emitted["payload"]["type"] == "codex"
    assert row == ("codex", "se", "PLAN-063", "W-1c")


def test_redaction_patterns_remove_sensitive_fragments() -> None:
    redacted = helix_db._redact_meta({"role": "se", "model": "gpt-5.4", "task_id": "sk-" + ("X" * 24), "plan_id": "PLAN-063", "sprint": "Bearer secret-token", "decision": "passed token=xyz", "cost_cents": 1.5, "duration_ms": 3210})

    assert redacted["task_id"] == "[REDACTED]"
    assert redacted["sprint"] == "[REDACTED]"
    assert redacted["decision"] == "passed [REDACTED]"
