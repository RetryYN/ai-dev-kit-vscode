from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path


HELIX_ROOT = Path(__file__).resolve().parents[3]


def _write_gate_checks(project_root: Path) -> None:
    helix_dir = project_root / ".helix"
    helix_dir.mkdir(parents=True, exist_ok=True)
    (helix_dir / "gate-checks.yaml").write_text(
        "G2:\n"
        "  name: G2 detector integration\n"
        "  static:\n"
        "  ai:\n"
        "G4:\n"
        "  name: G4 detector integration\n"
        "  static:\n"
        "  ai:\n"
        "G6:\n"
        "  name: G6 detector integration\n"
        "  static:\n"
        "  ai:\n",
        encoding="utf-8",
    )


def _write_phase(project_root: Path) -> None:
    (project_root / ".helix" / "phase.yaml").write_text(
        "current_phase: L6\n"
        "sprint:\n"
        "  drive: be\n"
        "  ui: false\n"
        "gates:\n"
        "  G1:\n"
        "    status: passed\n"
        "  G2:\n"
        "    status: passed\n"
        "  G3:\n"
        "    status: passed\n"
        "  G4:\n"
        "    status: passed\n"
        "  G5:\n"
        "    status: passed\n",
        encoding="utf-8",
    )


def _init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE detector_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            axis_id TEXT NOT NULL,
            detector_name TEXT NOT NULL,
            phase_gate TEXT,
            verdict TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            cost_ms INTEGER NOT NULL,
            raw_json TEXT NOT NULL,
            config_json TEXT NOT NULL,
            command TEXT NOT NULL,
            db_path TEXT NOT NULL
        );
        CREATE TABLE code_index (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            summary TEXT NOT NULL,
            path TEXT NOT NULL,
            line_no INTEGER NOT NULL,
            symbol_line INTEGER NOT NULL DEFAULT 0,
            bucket TEXT NOT NULL DEFAULT 'coverage_eligible'
        );
        CREATE TABLE routing_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT,
            source TEXT,
            decision TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    return conn


def _seed_code_index_case_mix(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("sample.load_data", "cli/lib", "snake", "cli/lib/mixed.py", 1, 1, "coverage_eligible"),
            ("sample.loadData", "cli/lib", "camel", "cli/lib/mixed.py", 2, 2, "coverage_eligible"),
        ],
    )


def _seed_code_index_orphan(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO code_index (id, domain, summary, path, line_no, symbol_line, bucket)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("sample.orphan", "cli/lib", "orphan", "cli/lib/orphan.py", 1, 1, "coverage_eligible"),
    )


def _seed_routing_history(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO routing_decisions (plan_id, source, decision, detail, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                "PLAN-063",
                "docs/plans/PLAN-063-helix-db-detector-system.md#/W-7",
                "carry",
                "recurring carry",
                "2026-05-12T00:00:00Z",
            ),
            (
                "PLAN-063",
                "docs/plans/PLAN-063-helix-db-detector-system.md#/W-7",
                "carry",
                "recurring carry",
                "2026-05-12T01:00:00Z",
            ),
        ],
    )


def _run_gate(project_root: Path, gate: str, *, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {
        "HOME": str(project_root / "home"),
        "HELIX_HOME": str(HELIX_ROOT),
        "HELIX_PROJECT_ROOT": str(project_root),
        "HELIX_DISABLE_FEEDBACK": "1",
        "PATH": f"{HELIX_ROOT / 'cli'}:{Path('/usr/bin')}:{Path('/bin')}",
    }
    (project_root / "home").mkdir(exist_ok=True)
    args = [str(HELIX_ROOT / "cli" / "helix-gate"), gate, "--static-only", "--readiness-mode", "skip"]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        cwd=str(project_root),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_gate_g2_auto_runs_expected_detectors_and_fail_closes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_gate_checks(project_root)
    _write_phase(project_root)
    conn = _init_db(project_root / ".helix" / "helix.db")
    try:
        _seed_code_index_case_mix(conn)
        conn.commit()
    finally:
        conn.close()

    completed = _run_gate(project_root, "G2")

    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert "[helix-gate] detector auto-run: G2" in output
    assert "axis-06" in output
    assert "=== G2 FAIL" in output


def test_gate_g4_auto_runs_expected_detectors_and_fail_closes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_gate_checks(project_root)
    _write_phase(project_root)
    conn = _init_db(project_root / ".helix" / "helix.db")
    try:
        _seed_code_index_orphan(conn)
        conn.commit()
    finally:
        conn.close()

    completed = _run_gate(project_root, "G4")

    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert "[helix-gate] detector auto-run: G4" in output
    assert "axis-01" in output
    assert "=== G4 FAIL" in output


def test_gate_g6_auto_runs_expected_detectors_and_fail_closes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_gate_checks(project_root)
    _write_phase(project_root)
    conn = _init_db(project_root / ".helix" / "helix.db")
    try:
        _seed_routing_history(conn)
        conn.commit()
    finally:
        conn.close()

    completed = _run_gate(project_root, "G6")

    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert "[helix-gate] detector auto-run: G6" in output
    assert "axis-05" in output
    assert "=== G6 FAIL" in output


def test_gate_skip_detectors_keeps_pass_when_detector_fixture_would_fail(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_gate_checks(project_root)
    _write_phase(project_root)
    conn = _init_db(project_root / ".helix" / "helix.db")
    try:
        _seed_code_index_case_mix(conn)
        conn.commit()
    finally:
        conn.close()

    completed = _run_gate(project_root, "G2", extra_args=["--skip-detectors"])

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0
    assert "detector auto-run skipped" in output
    assert "=== G2 PASS ===" in output
