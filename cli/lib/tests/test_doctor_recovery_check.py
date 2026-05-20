"""PLAN-098 doctor_recovery_check 単体/統合テスト.

契約: docs/plans/PLAN-098-recovery-plan-kind-normalization.md §9 §11.2-§11.3
DoD 検証: PLAN-098 §12.4-§12.5
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import doctor_recovery_check


def _write_recovery_plan(
    path: Path,
    *,
    plan_id: str,
    revised: str | None,
    kind: str = "recovery",
) -> None:
    frontmatter = [
        "---",
        f"plan_id: {plan_id}",
        f"kind: {kind}",
        "status: active",
    ]
    if revised is not None:
        frontmatter.append(f"revised: {revised}")
    frontmatter.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter + ["", "# recovery", ""]) + "\n", encoding="utf-8")


def _run_doctor(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    env["HOME"] = str(project_root / "home")
    return subprocess.run(
        [str(REPO_ROOT / "cli/helix-doctor"), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_run_check_recovery_freshness_reports_warning_rows(monkeypatch, tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.3 (recovery PLAN sweep と stale warning 集計)"""
    docs_dir = tmp_path / "docs" / "plans"
    fresh_revised = (datetime.now(UTC) - timedelta(days=5)).date().isoformat()
    stale_revised = (datetime.now(UTC) - timedelta(days=31)).date().isoformat()
    _write_recovery_plan(docs_dir / "PLAN-100-recovery-fresh.md", plan_id="PLAN-100", revised=fresh_revised)
    _write_recovery_plan(docs_dir / "PLAN-101-recovery-stale.md", plan_id="PLAN-101", revised=stale_revised)
    _write_recovery_plan(docs_dir / "PLAN-102-recovery-ignore.md", plan_id="PLAN-102", revised=stale_revised, kind="design")

    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    rows = doctor_recovery_check.run_check_recovery_freshness(max_age_days=30)

    assert [row["plan_id"] for row in rows] == ["PLAN-100", "PLAN-101"]
    assert [row["status"] for row in rows] == ["ok", "warning"]
    assert rows[1]["reason"] == "stale_recovery_plan"


def test_run_check_recovery_freshness_uses_mtime_fallback(monkeypatch, tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.2 (revised 不在時は mtime fallback)"""
    plan_path = tmp_path / "docs" / "plans" / "PLAN-103-recovery-mtime.md"
    _write_recovery_plan(plan_path, plan_id="PLAN-103", revised=None)
    stale_time = datetime.now(UTC) - timedelta(days=35)
    os.utime(plan_path, (stale_time.timestamp(), stale_time.timestamp()))

    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    rows = doctor_recovery_check.run_check_recovery_freshness(max_age_days=30)

    assert rows[0]["plan_id"] == "PLAN-103"
    assert rows[0]["status"] == "warning"
    assert rows[0]["age_days"] >= 35


def test_run_check_recovery_freshness_ignores_non_matching_filenames(monkeypatch, tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.3 (対象 glob 外は走査しない)"""
    docs_dir = tmp_path / "docs" / "plans"
    revised = (datetime.now(UTC) - timedelta(days=31)).date().isoformat()
    _write_recovery_plan(docs_dir / "PLAN-104-recovery-match.md", plan_id="PLAN-104", revised=revised)
    _write_recovery_plan(docs_dir / "PLAN-105-other.md", plan_id="PLAN-105", revised=revised)

    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    rows = doctor_recovery_check.run_check_recovery_freshness(max_age_days=30)

    assert [row["plan_id"] for row in rows] == ["PLAN-104"]


def test_helix_doctor_recovery_subcommand_warns_for_stale_plan(tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §12.4 (stale recovery で warn 表示 + exit 1)"""
    docs_dir = tmp_path / "docs" / "plans"
    stale_revised = (datetime.now(UTC) - timedelta(days=31)).date().isoformat()
    _write_recovery_plan(docs_dir / "PLAN-106-recovery-stale.md", plan_id="PLAN-106", revised=stale_revised)
    (tmp_path / "home").mkdir()

    result = _run_doctor(tmp_path, "check_recovery_plan_freshness")

    assert result.returncode == 1
    assert "[recovery freshness]" in result.stdout
    assert "△ recovery plan freshness" in result.stdout
    assert "PLAN-106" in result.stdout


def test_helix_doctor_recovery_subcommand_passes_for_fresh_plan(tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §12.4 (fresh recovery のみなら exit 0)"""
    docs_dir = tmp_path / "docs" / "plans"
    fresh_revised = (datetime.now(UTC) - timedelta(days=2)).date().isoformat()
    _write_recovery_plan(docs_dir / "PLAN-107-recovery-fresh.md", plan_id="PLAN-107", revised=fresh_revised)
    (tmp_path / "home").mkdir()

    result = _run_doctor(tmp_path, "check_recovery_plan_freshness")

    assert result.returncode == 0
    assert "✓ recovery plan freshness" in result.stdout
    assert "checked: 1" in result.stdout
