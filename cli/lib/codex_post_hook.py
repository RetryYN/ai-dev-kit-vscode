#!/usr/bin/env python3
"""Post-processing helpers for helix-codex TL review output."""

from __future__ import annotations

import argparse
import io
import re
import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


DIMENSIONS = tuple(helix_db.ACCURACY_SCORE_DIMENSIONS)
OVERALL_SCORES_RE = re.compile(r'"overall_scores"\s*:\s*\[(.*?)\]', re.DOTALL)
SCORE_RE = re.compile(
    r'\{\s*"dimension":\s*"(density|depth|breadth|accuracy|maintainability)"\s*,\s*"level":\s*(\d)\s*,\s*"comment":\s*"([^"]*)"\s*\}',
    re.DOTALL,
)


def _extract_complete_block(text: str) -> list[dict[str, object]] | None:
    entries = [
        {
            "dimension": match.group(1),
            "level": int(match.group(2)),
            "comment": match.group(3),
        }
        for match in SCORE_RE.finditer(text)
    ]
    if len(entries) < len(DIMENSIONS):
        return None

    for start in range(len(entries)):
        seen: dict[str, dict[str, object]] = {}
        for entry in entries[start:]:
            dimension = str(entry["dimension"])
            if dimension in seen:
                break
            seen[dimension] = entry
            if len(seen) == len(DIMENSIONS):
                return [seen[dimension] for dimension in DIMENSIONS]
    return None


def extract_overall_scores_from_text(text: str) -> list[dict[str, object]] | None:
    for block in OVERALL_SCORES_RE.findall(text):
        scores = _extract_complete_block(block)
        if scores is not None:
            return scores
    return _extract_complete_block(text)


def _evidence(run_id: str) -> str:
    return f"source=helix-codex-post-hook\nrun_id={run_id}"


def _has_existing_score(
    db_path: str,
    *,
    plan_id: str,
    gate: str,
    dimension: str,
    reviewer: str,
    evidence: str,
) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM accuracy_score
            WHERE plan_id = ?
              AND gate = ?
              AND dimension = ?
              AND reviewer = ?
              AND evidence = ?
            LIMIT 1
            """,
            (plan_id, gate, dimension, reviewer, evidence),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def insert_accuracy_scores(
    db_path: str,
    *,
    plan_id: str,
    run_id: str,
    scores: list[dict[str, object]],
    gate: str = "PLAN_REVIEW",
    reviewer: str = "codex-tl",
) -> int:
    helix_db._prepare_db_path(db_path)
    conn = helix_db._connect(db_path)
    try:
        helix_db._ensure_schema(conn)
    finally:
        conn.close()

    evidence = _evidence(run_id)
    inserted = 0
    for score in scores:
        dimension = str(score["dimension"])
        if _has_existing_score(
            db_path,
            plan_id=plan_id,
            gate=gate,
            dimension=dimension,
            reviewer=reviewer,
            evidence=evidence,
        ):
            continue
        helix_db.record_accuracy_score(
            db_path,
            plan_id,
            gate,
            dimension,
            int(score["level"]),
            comment=str(score["comment"]),
            evidence=evidence,
            reviewer=reviewer,
        )
        inserted += 1
    return inserted


def record_post_review_scores(
    db_path: str,
    *,
    plan_id: str,
    run_id: str,
    stdout_text: str = "",
    audit_text: str = "",
    stderr: io.TextIOBase | None = None,
) -> int:
    stream = stderr or sys.stderr
    try:
        scores = extract_overall_scores_from_text(stdout_text)
        if scores is None and audit_text:
            scores = extract_overall_scores_from_text(audit_text)
        if scores is None:
            print("WARN: codex post-hook skipped (overall_scores not found)", file=stream)
            return 0
        return insert_accuracy_scores(db_path, plan_id=plan_id, run_id=run_id, scores=scores)
    except Exception as exc:  # pragma: no cover - fail-open wrapper
        print(f"WARN: codex post-hook skipped: {exc}", file=stream)
        return 0


def record_post_review_scores_from_files(
    db_path: str,
    *,
    plan_id: str,
    run_id: str,
    stdout_file: str | None = None,
    audit_log: str | None = None,
    stderr: io.TextIOBase | None = None,
) -> int:
    stdout_text = ""
    audit_text = ""
    if stdout_file and Path(stdout_file).is_file():
        stdout_text = Path(stdout_file).read_text(encoding="utf-8")
    if audit_log and Path(audit_log).is_file():
        audit_text = Path(audit_log).read_text(encoding="utf-8")
    return record_post_review_scores(
        db_path,
        plan_id=plan_id,
        run_id=run_id,
        stdout_text=stdout_text,
        audit_text=audit_text,
        stderr=stderr,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist overall_scores from helix-codex TL review output.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--stdout-file")
    parser.add_argument("--audit-log")
    args = parser.parse_args()

    record_post_review_scores_from_files(
        args.db,
        plan_id=args.plan_id,
        run_id=args.run_id,
        stdout_file=args.stdout_file,
        audit_log=args.audit_log,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
