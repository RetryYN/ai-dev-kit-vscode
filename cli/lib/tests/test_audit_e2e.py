"""PLAN-002 e2e 統合テスト (最小)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import helix_db


SCRIPT_DIR = Path(__file__).parent.parent.parent
HELIX_AUDIT = SCRIPT_DIR / "helix-audit"


def _setup_workspace() -> tuple[Path, Path]:
    ws = Path(tempfile.mkdtemp(prefix="helix-e2e-"))
    (ws / ".helix" / "audit").mkdir(parents=True)
    (ws / ".helix" / "locks").mkdir(parents=True)
    db = ws / ".helix" / "helix.db"
    helix_db.init_db(str(db))
    return ws, db


def _run_audit(ws: Path, db: Path, *args: str):
    env = os.environ.copy()
    env["HELIX_DIR"] = str(ws / ".helix")
    env["HELIX_PROJECT_ROOT"] = str(ws)
    env["HELIX_DB_PATH"] = str(db)
    return subprocess.run(
        [str(HELIX_AUDIT), *args],
        env=env,
        cwd=str(ws),
        capture_output=True,
        text=True,
    )


def _make_yaml(ws: Path, candidate_id: str = "src/a.py", scope_hash: str = "a" * 64) -> Path:
    p = ws / "decisions.yaml"
    p.write_text(
        f"""\
version: 1
metadata:
  scope_hash: "{scope_hash}"
  source_hash: "{'b' * 64}"
  schema_version: 1
decisions:
  - candidate_id: {candidate_id}
    schema_version: 1
    scope_hash: "{scope_hash}"
    decision: keep
    rationale: e2e test
    evidence:
      source: {candidate_id}
      hash: deadbeef
      redacted: true
    fail_safe_action: skip
""",
        encoding="utf-8",
    )
    return p


def test_e2e_a1_dry_run_and_import():
    ws, db = _setup_workspace()
    yaml_path = _make_yaml(ws)

    r = _run_audit(ws, db, "a1", "import", "--file", str(yaml_path), "--dry-run")
    assert r.returncode == 0, f"dry-run failed: {r.stderr}"

    r = _run_audit(ws, db, "a1", "import", "--file", str(yaml_path))
    assert r.returncode == 0, f"import failed: {r.stderr}"

    r = _run_audit(ws, db, "a1", "status")
    assert r.returncode == 0
    assert "src/a.py" in r.stdout


def test_e2e_a1_idempotent():
    ws, db = _setup_workspace()
    yaml_path = _make_yaml(ws)

    _run_audit(ws, db, "a1", "import", "--file", str(yaml_path))
    r = _run_audit(ws, db, "a1", "import", "--file", str(yaml_path))
    assert r.returncode == 0
    assert '"case_a"' in r.stdout


def test_e2e_validation_error_no_db_state():
    ws, db = _setup_workspace()
    bad = ws / "bad.yaml"
    bad.write_text("version: 99\ndecisions: []\n", encoding="utf-8")

    r = _run_audit(ws, db, "a1", "import", "--file", str(bad))
    assert r.returncode == 1

    import sqlite3

    conn = sqlite3.connect(str(db))
    try:
        ar = conn.execute("SELECT COUNT(*) FROM audit_decisions").fetchone()[0]
        ir = conn.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0]
    finally:
        conn.close()
    assert ar == 0
    assert ir == 0
