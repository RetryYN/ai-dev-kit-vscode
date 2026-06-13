"""Tests for helix-doctor mode/phase consistency check (PLAN-050 W-3)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_doctor(tmp_path: Path, mode: str, phase: str, extra_phase_yaml: str = "") -> str:
    helix_dir = tmp_path / ".helix"
    helix_dir.mkdir()
    (helix_dir / "phase.yaml").write_text(
        f"current_mode: {mode}\ncurrent_phase: {phase}\n{extra_phase_yaml}",
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "PROJECT_ROOT": str(tmp_path),
        "HELIX_PROJECT_ROOT": str(tmp_path),
        "HELIX_HOME": str(REPO_ROOT),
        "PATH": "/usr/bin:/bin",
    }
    result = subprocess.run(
        [str(REPO_ROOT / "cli" / "helix-doctor")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return result.stdout + result.stderr


def test_phase_mode_forward_l_phase_pass(tmp_path: Path) -> None:
    output = _run_doctor(tmp_path, "forward", "L4")
    assert "phase_mode_consistency" in output
    assert "⚠ phase_mode_consistency" not in output


def test_phase_mode_reverse_r_phase_pass(tmp_path: Path) -> None:
    output = _run_doctor(tmp_path, "reverse", "R2")
    assert "⚠ phase_mode_consistency" not in output


def test_phase_mode_scrum_s_phase_pass(tmp_path: Path) -> None:
    output = _run_doctor(tmp_path, "scrum", "S1")
    assert "⚠ phase_mode_consistency" not in output


def test_phase_mode_discovery_d_phase_pass(tmp_path: Path) -> None:
    output = _run_doctor(tmp_path, "discovery", "D1")
    assert "⚠ phase_mode_consistency" not in output


def test_phase_mode_mismatch_warns(tmp_path: Path) -> None:
    output = _run_doctor(tmp_path, "reverse", "L1")
    assert "⚠ phase_mode_consistency" in output
    assert "reverse" in output
    assert "L1" in output


def test_phase_gate_progress_without_gate_evidence_does_not_warn(tmp_path: Path) -> None:
    output = _run_doctor(tmp_path, "forward", "L4")
    assert "phase_gate_progress" in output
    assert "⚠ phase_gate_progress" not in output


def test_phase_gate_progress_warns_when_g6_passed_but_phase_lags(tmp_path: Path) -> None:
    output = _run_doctor(
        tmp_path,
        "forward",
        "L4",
        "gates:\n  G6:\n    status: passed\n",
    )
    assert "⚠ phase_gate_progress" in output
    assert "G6 passed" in output
    assert "current_phase=L4" in output
    assert "L6" in output


def test_phase_gate_progress_passes_when_g6_matches_l6_focus(tmp_path: Path) -> None:
    output = _run_doctor(
        tmp_path,
        "forward",
        "L6",
        "gates:\n  G6:\n    status: passed\n",
    )
    assert "✓ phase_gate_progress" in output
    assert "⚠ phase_gate_progress" not in output


def test_phase_gate_progress_passes_when_phase_is_ahead(tmp_path: Path) -> None:
    output = _run_doctor(
        tmp_path,
        "forward",
        "L7",
        "gates:\n  G6:\n    status: passed\n",
    )
    assert "✓ phase_gate_progress" in output
    assert "⚠ phase_gate_progress" not in output
