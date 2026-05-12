from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _history_counts(conn: sqlite3.Connection) -> list[int]:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='detector_runs'"
    ).fetchone()
    if row is None:
        return []

    rows = conn.execute(
        """
        SELECT raw_json, findings_json
        FROM detector_runs
        WHERE axis_id = ?
        ORDER BY run_id
        """,
        ("axis-02",),
    ).fetchall()

    counts: list[int] = []
    for row in rows:
        payload: dict[str, Any] = {}
        for key in ("raw_json", "findings_json"):
            raw_value = row[key]
            if not raw_value:
                continue
            try:
                parsed = json.loads(raw_value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                payload = parsed
                break
        count_value = payload.get("current_uncovered")
        if count_value is None:
            count_value = payload.get("curr_uncovered")
        if count_value is None:
            continue
        try:
            counts.append(int(count_value))
        except (TypeError, ValueError):
            continue
    return counts


def _consecutive_worsening_streak(counts: list[int]) -> int:
    if len(counts) < 2:
        return 0
    streak = 0
    for previous, current in zip(counts[:-1], counts[1:]):
        if current > previous:
            streak += 1
        else:
            streak = 0
    return streak


def _run_uncovered_stats(root: Path) -> dict[str, Any]:
    command = [
        str(root / "cli" / "helix"),
        "code",
        "stats",
        "--uncovered",
        "--bucket",
        "coverage_eligible",
        "--json",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        cwd=root,
        env={**os.environ, "HELIX_PROJECT_ROOT": str(root)},
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"helix code stats --uncovered failed: returncode={completed.returncode}"
        )
    payload = json.loads(completed.stdout or "{}")
    if not isinstance(payload, dict):
        raise RuntimeError("helix code stats --uncovered did not return an object")
    return payload


class Axis02CoverageErosion(BaseDetector):
    id = "axis-02"
    name = "coverage erosion"
    phase_gate = "G4"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            history = _history_counts(conn)
        finally:
            conn.close()

        root = _project_root(db_path)
        if not history:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": "no prior detector_runs history for axis-02",
                    "project_root": str(root),
                },
            )
        try:
            payload = _run_uncovered_stats(root)
        except Exception as exc:  # pragma: no cover - exercised via dashboard/empty-db path
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": str(exc),
                    "project_root": str(root),
                },
            )
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        current_uncovered = len(items) if items else int(summary.get("eligible", 0)) - int(summary.get("covered", 0))
        current_uncovered = max(0, current_uncovered)

        previous_uncovered = history[-1] if history else None
        delta = current_uncovered - previous_uncovered if previous_uncovered is not None else 0

        findings: list[dict[str, Any]] = []
        verdict = "passed"
        if previous_uncovered is not None and current_uncovered > previous_uncovered:
            streak_counts = history + [current_uncovered]
            worsening_streak = _consecutive_worsening_streak(streak_counts)
            findings.append(
                {
                    "path": "cli/lib/*",
                    "prev_uncovered": previous_uncovered,
                    "curr_uncovered": current_uncovered,
                    "delta": delta,
                }
            )
            if worsening_streak >= 3:
                verdict = "failed"
            else:
                verdict = "passed"

        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "current_uncovered": current_uncovered,
                "previous_uncovered": previous_uncovered,
                "delta": delta,
                "worsening_streak": _consecutive_worsening_streak(history + [current_uncovered]) if history else 0,
                "stats_summary": summary,
            },
        )
