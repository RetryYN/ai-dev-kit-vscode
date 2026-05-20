import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "cli" / "helix-heartbeat-scheduler"


def _run_scheduler(tmp_path: Path, handover_payload: dict, budget_payload: dict) -> dict:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    handover_path = tmp_path / "handover.json"
    budget_path = tmp_path / "budget.json"
    handover_path.write_text(json.dumps(handover_payload), encoding="utf-8")
    budget_path.write_text(json.dumps(budget_payload), encoding="utf-8")

    helix_stub = fake_bin / "helix"
    helix_stub.write_text(
        """#!/bin/bash
set -euo pipefail
if [[ "${1:-}" == "handover" && "${2:-}" == "status" && "${3:-}" == "--json" ]]; then
  cat "$HELIX_HANDOVER_JSON_FILE"
  exit 0
fi
if [[ "${1:-}" == "budget" && "${2:-}" == "status" && "${3:-}" == "--json" ]]; then
  cat "$HELIX_BUDGET_JSON_FILE"
  exit 0
fi
echo "unexpected args: $*" >&2
exit 2
""",
        encoding="utf-8",
    )
    helix_stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["HELIX_HANDOVER_JSON_FILE"] = str(handover_path)
    env["HELIX_BUDGET_JSON_FILE"] = str(budget_path)

    proc = subprocess.run(
        [str(SCRIPT), "--json"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_adaptive_interval_healthy(tmp_path: Path) -> None:
    result = _run_scheduler(
        tmp_path,
        handover_payload={"files": {"pending_count": 2}},
        budget_payload={
            "claude": {"weekly_remaining_pct": 70},
            "codex": {"weekly_used_pct": 20},
            "recommendations": [],
        },
    )

    assert result["carry_count"] == 2
    assert result["budget_tier"] == "healthy"
    assert result["interval_minutes"] == 15
    assert result["schedulewakeup_candidate"]["after_minutes"] == 15


def test_critical(tmp_path: Path) -> None:
    result = _run_scheduler(
        tmp_path,
        handover_payload={"files": {"pending_count": 1}},
        budget_payload={
            "claude": {"weekly_remaining_pct": 40},
            "codex": {"weekly_used_pct": 10},
            "recommendations": [{"severity": "critical", "message": "budget critical"}],
        },
    )

    assert result["budget_tier"] == "critical"
    assert result["interval_minutes"] == 5


def test_no_carry(tmp_path: Path) -> None:
    result = _run_scheduler(
        tmp_path,
        handover_payload={"files": {"pending_count": 0}},
        budget_payload={
            "claude": {"weekly_remaining_pct": 70},
            "codex": {"weekly_used_pct": 20},
            "recommendations": [],
        },
    )

    assert result["carry_count"] == 0
    assert result["interval_minutes"] is None
    assert result["next_action"] == "skip"
    assert result["schedulewakeup_candidate"] is None


def test_low(tmp_path: Path) -> None:
    result = _run_scheduler(
        tmp_path,
        handover_payload={"files": {"pending_count": 3}},
        budget_payload={
            "claude": {"weekly_remaining_pct": 25},
            "codex": {"weekly_used_pct": 40},
            "recommendations": [],
        },
    )

    assert result["budget_tier"] == "low"
    assert result["interval_minutes"] == 30
