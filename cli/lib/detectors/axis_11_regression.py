from __future__ import annotations

import json
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult, STUB_REASON


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _commit_order(conn: sqlite3.Connection) -> list[str]:
    if not _table_exists(conn, "test_baseline"):
        return []
    rows = conn.execute(
        """
        SELECT commit_sha, MAX(timestamp) AS latest_timestamp, MAX(id) AS latest_id
        FROM test_baseline
        GROUP BY commit_sha
        ORDER BY latest_timestamp, latest_id
        """
    ).fetchall()
    return [str(row["commit_sha"]) for row in rows]


def _baseline_rows(conn: sqlite3.Connection, commit_sha: str) -> dict[tuple[str, str], dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, commit_sha, timestamp, suite, test_name, status
        FROM test_baseline
        WHERE commit_sha = ?
        ORDER BY suite, test_name, id
        """,
        (commit_sha,),
    ).fetchall()
    return {
        (str(row["suite"]), str(row["test_name"])): {key: row[key] for key in row.keys()}
        for row in rows
    }


def _flaky_history_window(
    conn: sqlite3.Connection,
    *,
    suite: str,
    test_name: str,
    current_id: int,
) -> list[str]:
    rows = conn.execute(
        """
        SELECT status
        FROM test_baseline
        WHERE suite = ? AND test_name = ? AND id <> ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 5
        """,
        (suite, test_name, current_id),
    ).fetchall()
    return [str(row["status"]) for row in rows]


def _pass_to_fail_findings(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    commits = _commit_order(conn)
    if len(commits) < 2:
        return [], {}
    previous_commit = commits[-2]
    current_commit = commits[-1]
    previous_rows = _baseline_rows(conn, previous_commit)
    current_rows = _baseline_rows(conn, current_commit)

    findings: list[dict[str, Any]] = []
    for key in sorted(set(previous_rows) & set(current_rows)):
        previous = previous_rows[key]
        current = current_rows[key]
        if str(previous["status"]) != "PASS" or str(current["status"]) != "FAIL":
            continue
        window = _flaky_history_window(
            conn,
            suite=str(current["suite"]),
            test_name=str(current["test_name"]),
            current_id=int(current["id"]),
        )
        severity = "warning" if any(status == "FAIL" for status in window) else "critical"
        findings.append(
            {
                "kind": "test_pass_to_fail",
                "detail": f"{current['suite']}::{current['test_name']} {previous_commit}:PASS -> {current_commit}:FAIL",
                "severity": severity,
                "suite": current["suite"],
                "test_name": current["test_name"],
                "previous_commit": previous_commit,
                "current_commit": current_commit,
            }
        )

    return findings, {
        "previous_commit": previous_commit,
        "current_commit": current_commit,
        "previous_test_count": len(previous_rows),
        "current_test_count": len(current_rows),
    }


def _contract_diff_findings(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(conn, "contract_entries"):
        return []
    rows = conn.execute(
        """
        SELECT id, source_path, symbol_id, schema_hash, breaking_change_flag
        FROM contract_entries
        ORDER BY COALESCE(symbol_id, source_path), id
        """
    ).fetchall()
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        key = str(row["symbol_id"] or row["source_path"])
        grouped[key].append(row)

    findings: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        previous = group[-2]
        current = group[-1]
        previous_hash = str(previous["schema_hash"] or "")
        current_hash = str(current["schema_hash"] or "")
        previous_breaking = int(previous["breaking_change_flag"] or 0)
        current_breaking = int(current["breaking_change_flag"] or 0)
        if previous_hash == current_hash and previous_breaking == current_breaking:
            continue
        severity = "critical" if current_breaking > previous_breaking or current_breaking == 1 else "warning"
        findings.append(
            {
                "kind": "contract_diff",
                "detail": (
                    f"{key} schema_hash {previous_hash or '-'} -> {current_hash or '-'}, "
                    f"breaking_change_flag {previous_breaking} -> {current_breaking}"
                ),
                "severity": severity,
                "source_path": current["source_path"],
            }
        )
    return findings


def _parse_raw_json(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _silent_error_findings(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(conn, "detector_runs"):
        return []
    rows = conn.execute(
        """
        SELECT axis_id, verdict, raw_json
        FROM detector_runs
        ORDER BY axis_id, run_id
        """
    ).fetchall()
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        raw_payload = _parse_raw_json(row["raw_json"])
        if raw_payload.get("reason") == STUB_REASON:
            continue
        grouped[str(row["axis_id"])].append(row)

    findings: list[dict[str, Any]] = []
    for axis_id, group in sorted(grouped.items()):
        streak = 0
        for row in reversed(group):
            if str(row["verdict"]) != "blocked":
                break
            streak += 1
        if streak < 2:
            continue
        severity = "critical" if streak >= 3 else "warning"
        findings.append(
            {
                "kind": "silent_error_increase",
                "detail": f"{axis_id} has {streak} consecutive blocked detector runs",
                "severity": severity,
                "axis_id": axis_id,
            }
        )
    return findings


class Axis11RegressionDetection(BaseDetector):
    id = "axis-11"
    name = "regression detection"
    phase_gate = "G6"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        conn = helix_db.get_connection(target_db)
        try:
            baseline_findings, baseline_meta = _pass_to_fail_findings(conn)
            contract_findings = _contract_diff_findings(conn)
            silent_error_findings = _silent_error_findings(conn)
        finally:
            conn.close()

        findings = baseline_findings + contract_findings + silent_error_findings
        if not findings and not baseline_meta and not contract_findings and not silent_error_findings:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={"reason": "insufficient regression history"},
            )

        findings.sort(key=lambda item: (item["kind"], item["severity"], item["detail"]))
        verdict = "failed" if any(item["severity"] == "critical" for item in findings) else "passed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                **baseline_meta,
                "pass_to_fail_count": len(baseline_findings),
                "contract_diff_count": len(contract_findings),
                "silent_error_count": len(silent_error_findings),
            },
        )
