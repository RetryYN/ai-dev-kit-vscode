from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult

try:
    from ..yaml_parser import parse_yaml  # type: ignore
except Exception:  # pragma: no cover - fallback for direct script execution
    from yaml_parser import parse_yaml  # type: ignore


PLAN_RE = re.compile(r"\bPLAN-\d{3}\b")


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _audit_findings_path(root: Path) -> Path:
    return root / ".helix" / "audit" / "deferred-findings.yaml"


def _load_deferred_findings(root: Path) -> list[dict[str, Any]]:
    path = _audit_findings_path(root)
    if not path.is_file():
        return []
    parsed = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        return []
    findings = parsed.get("findings")
    if not isinstance(findings, list):
        return []
    return [item for item in findings if isinstance(item, dict)]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _row_text(row: dict[str, Any]) -> str:
    return " ".join(_stringify(value) for value in row.values() if value is not None).lower()


def _extract_plan_id(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        match = PLAN_RE.search(_stringify(value))
        if match:
            return match.group(0)
    return None


def _normalize_source(*values: Any) -> str:
    for value in values:
        text = _stringify(value).strip()
        if text:
            return text
    return "unknown"


def _normalize_kind(value: Any, *, fallback: str) -> str:
    text = _stringify(value).strip().lower()
    if not text:
        return fallback
    if "retro" in text and "carry" in text:
        return "retro_carry"
    if "carry" in text:
        return "carry"
    if "defer" in text:
        return "deferred"
    if "debt" in text:
        return "debt"
    return text.replace(" ", "_")


def _finding_target(finding: dict[str, Any]) -> dict[str, Any]:
    target = finding.get("target")
    return target if isinstance(target, dict) else {}


def _finding_carry_occurrence_count(finding: dict[str, Any]) -> int:
    carry_chain = finding.get("carry_chain")
    carry_count = len(carry_chain) if isinstance(carry_chain, list) else 0
    target = _finding_target(finding)
    status = str(finding.get("status") or "").strip().lower()
    if status == "carried" or target.get("plan_id") or target.get("phase"):
        carry_count += 1
    return carry_count


def _is_unresolved_carry(finding: dict[str, Any]) -> bool:
    status = str(finding.get("status") or "").strip().lower()
    if status == "resolved":
        return False
    return _finding_carry_occurrence_count(finding) > 0


def _finding_lineage(finding: dict[str, Any]) -> tuple[str, str, str | None]:
    current = finding.get("current") if isinstance(finding.get("current"), dict) else {}
    origin = finding.get("origin") if isinstance(finding.get("origin"), dict) else {}
    target = _finding_target(finding)
    plan_id = _extract_plan_id(
        finding.get("plan_id"),
        current.get("plan_id"),
        origin.get("plan_id"),
        target.get("plan_id"),
        finding.get("source"),
    )
    source = _normalize_source(
        finding.get("source"),
        finding.get("title"),
        finding.get("evidence"),
    )
    kind = _normalize_kind(finding.get("kind"), fallback="deferred_finding")
    return kind, source, plan_id


def _is_relevant_routing_row(row: dict[str, Any]) -> bool:
    text = _row_text(row)
    return any(token in text for token in ("retro carry", "deferred", "carry", "debt"))


def _routing_lineage(row: dict[str, Any]) -> tuple[str, str, str | None]:
    text = _row_text(row)
    kind = _normalize_kind(
        row.get("kind") or row.get("decision") or row.get("type") or row.get("status") or text,
        fallback="carry",
    )
    source = _normalize_source(
        row.get("source"),
        row.get("path"),
        row.get("source_path"),
        row.get("file_path"),
        row.get("detail"),
        row.get("title"),
    )
    plan_id = _extract_plan_id(
        row.get("plan_id"),
        row.get("current_plan_id"),
        row.get("target_plan_id"),
        row.get("detail"),
        row.get("decision"),
        text,
    )
    return kind, source, plan_id


def _routing_occurrences(conn: sqlite3.Connection) -> tuple[dict[tuple[str, str, str | None], int], int]:
    if not _table_exists(conn, "routing_decisions"):
        return {}, 0
    rows = conn.execute("SELECT * FROM routing_decisions ORDER BY rowid").fetchall()
    counts: dict[tuple[str, str, str | None], int] = defaultdict(int)
    relevant_rows = 0
    for row in rows:
        item = {key: row[key] for key in row.keys()}
        if not _is_relevant_routing_row(item):
            continue
        relevant_rows += 1
        counts[_routing_lineage(item)] += 1
    return dict(counts), relevant_rows


def _history_unresolved_counts(conn: sqlite3.Connection) -> list[int]:
    if not _table_exists(conn, "detector_runs"):
        return []
    rows = conn.execute(
        """
        SELECT raw_json
        FROM detector_runs
        WHERE axis_id = ?
        ORDER BY run_id
        """,
        ("axis-05",),
    ).fetchall()
    counts: list[int] = []
    for row in rows:
        raw_json = row["raw_json"]
        if not raw_json:
            continue
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        value = payload.get("current_unresolved_carry_count")
        if value is None:
            value = payload.get("unresolved_carry_count")
        if value is None:
            continue
        try:
            counts.append(int(value))
        except (TypeError, ValueError):
            continue
    return counts


class Axis05PlanDebtLoop(BaseDetector):
    id = "axis-05"
    name = "plan debt loop"
    phase_gate = "G6"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        root = _project_root(db_path)
        try:
            deferred_findings = _load_deferred_findings(root)
        except Exception as exc:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={"reason": str(exc), "project_root": str(root)},
            )

        conn = helix_db.get_connection(target_db)
        try:
            routing_counts, routing_rows_scanned = _routing_occurrences(conn)
            history = _history_unresolved_counts(conn)
        finally:
            conn.close()

        yaml_counts: dict[tuple[str, str, str | None], int] = {}
        unresolved_carry_count = 0
        for finding in deferred_findings:
            occurrence_count = _finding_carry_occurrence_count(finding)
            if occurrence_count > 0:
                yaml_counts[_finding_lineage(finding)] = max(
                    yaml_counts.get(_finding_lineage(finding), 0),
                    occurrence_count,
                )
            if _is_unresolved_carry(finding):
                unresolved_carry_count += 1

        combined_keys = sorted(set(yaml_counts) | set(routing_counts))
        if not combined_keys and unresolved_carry_count == 0:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={
                    "reason": "no deferred carry data or routing history",
                    "project_root": str(root),
                },
            )

        findings: list[dict[str, Any]] = []
        for key in combined_keys:
            occurrence_count = max(yaml_counts.get(key, 0), routing_counts.get(key, 0))
            if occurrence_count < 2:
                continue
            _lineage_kind, source, plan_id = key
            findings.append(
                {
                    "kind": "recurring_debt",
                    "plan_id": plan_id,
                    "source": source,
                    "occurrence_count": occurrence_count,
                }
            )

        previous_unresolved = history[-1] if history else None
        if previous_unresolved is not None and unresolved_carry_count > previous_unresolved:
            findings.append(
                {
                    "kind": "carry_increase",
                    "source": str(_audit_findings_path(root).relative_to(root)),
                    "occurrence_count": unresolved_carry_count,
                    "previous_occurrence_count": previous_unresolved,
                }
            )

        findings.sort(
            key=lambda item: (
                item["kind"],
                str(item.get("plan_id") or ""),
                str(item.get("source") or ""),
            )
        )
        verdict = "failed" if any(item["kind"] == "recurring_debt" for item in findings) else "passed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "project_root": str(root),
                "yaml_findings_scanned": len(deferred_findings),
                "routing_rows_scanned": routing_rows_scanned,
                "current_unresolved_carry_count": unresolved_carry_count,
                "previous_unresolved_carry_count": previous_unresolved,
                "recurring_lineage_count": sum(1 for item in findings if item["kind"] == "recurring_debt"),
            },
        )
