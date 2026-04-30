#!/usr/bin/env python3
"""
.helix/reviews/plans/PLAN-*.json から high/medium 重要度の finding を
.helix/audit/deferred-findings.yaml に import する。

severity -> level mapping:
  critical -> P0
  high     -> P1
  medium   -> P2
  low      -> P3 (skip - 任意 carry)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = PROJECT_ROOT / "cli" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from deferred_findings import SEVERITY_TO_LEVEL, add_finding


DEFAULT_REVIEWS_DIR = Path(".helix/reviews/plans")
DEFAULT_OUTPUT = Path(".helix/audit/deferred-findings.yaml")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import review findings into .helix/audit/deferred-findings.yaml",
    )
    parser.add_argument("--reviews-dir", type=Path, default=DEFAULT_REVIEWS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-low", action="store_true", help="include low severity as P3")
    parser.add_argument("--dry-run", action="store_true", help="count findings without writing YAML")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output YAML")
    return parser.parse_args(argv)


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_plan(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    findings = data.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError(f"{path}: findings must be a list")
    return data


def build_finding(plan_id: str, index: int, finding: dict[str, Any]) -> dict[str, Any] | None:
    severity = str(finding.get("severity", "")).lower()
    if severity not in SEVERITY_TO_LEVEL:
        raise ValueError(f"{plan_id} findings[{index}]: invalid severity: {severity}")
    phase = str(finding.get("helix_phase") or "L?")
    return {
        "plan_id": plan_id,
        "phase": phase,
        "severity": severity,
        "title": finding["title"],
        "body": finding["body"],
        "recommendation": finding["recommendation"],
        "dimension_scores": finding.get("dimension_scores", []),
        "source": f".helix/reviews/plans/{plan_id}.json#/findings/{index}",
        "origin": {"plan_id": plan_id, "phase": phase},
        "current": {"plan_id": plan_id, "phase": phase},
        "target": None,
    }


def collect_findings(reviews_dir: Path, include_low: bool) -> tuple[list[dict[str, Any]], Counter[str], int]:
    imported: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    skipped = 0
    for path in sorted(reviews_dir.glob("PLAN-*.json")):
        plan = load_plan(path)
        plan_id = path.stem
        for index, raw_finding in enumerate(plan["findings"]):
            if not isinstance(raw_finding, dict):
                raise ValueError(f"{path}: findings[{index}] must be an object")
            severity = str(raw_finding.get("severity", "")).lower()
            if severity == "low" and not include_low:
                skipped += 1
                continue
            finding = build_finding(plan_id, index, raw_finding)
            if finding is None:
                continue
            counts[SEVERITY_TO_LEVEL[finding["severity"]]] += 1
            imported.append(finding)
    return imported, counts, skipped


def format_summary(counts: Counter[str], skipped: int) -> str:
    imported = sum(counts.values())
    level_parts = []
    if counts.get("P0"):
        level_parts.append(f"P0={counts['P0']}")
    level_parts.extend(
        [
            f"P1={counts['P1']}",
            f"P2={counts['P2']}",
            f"P3={counts['P3']}",
        ]
    )
    return f"imported: {imported} ({', '.join(level_parts)} skipped={skipped})"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reviews_dir = project_path(args.reviews_dir)
    output = project_path(args.output)
    if not reviews_dir.is_dir():
        print(f"reviews dir not found: {reviews_dir}", file=sys.stderr)
        return 2

    imported, counts, skipped = collect_findings(reviews_dir, args.include_low)
    summary = format_summary(counts, skipped)
    if args.dry_run:
        print(summary)
        return 0

    if output.exists() and not args.force:
        print(f"output already exists, rerun with --force to overwrite: {output}", file=sys.stderr)
        return 2
    if output.exists():
        output.unlink()
    for finding in imported:
        add_finding(output, finding)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
