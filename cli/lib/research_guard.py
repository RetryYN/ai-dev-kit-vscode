#!/usr/bin/env python3
"""Fail-close checks for the HELIX G1R research gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REPORT_PATTERNS = (
    "docs/research/**/*.md",
    ".helix/research/**/*.md",
    "docs/features/**/D-RES/**/*.md",
    "docs/shared/**/D-RES/**/*.md",
    "docs/platform/**/D-RES/**/*.md",
)

ARCHIVE_PARTS = {"archive", "generated"}
SOURCE_RE = re.compile(r"https?://|(?:^|\n)\s*#+\s*(?:Sources?|References?|出典|根拠)", re.IGNORECASE)
DECISION_RE = re.compile(r"採用|不採用|選定|推奨|判断|decision|adopt|reject|recommended", re.IGNORECASE)
OPEN_BLOCKER_LINE_RE = re.compile(r"^\s*open[_ -]?blockers?\s*[:=]\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
UNCHECKED_BLOCKER_RE = re.compile(r"^\s*[-*]\s+\[\s\].*(blocker|blocked|未解決|要確認)", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class GuardFinding:
    code: str
    message: str
    path: str = ""


def _is_active_report(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts
    return not any(part in ARCHIVE_PARTS for part in rel_parts)


def find_reports(root: Path) -> list[Path]:
    reports: dict[str, Path] = {}
    for pattern in REPORT_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file() and _is_active_report(path, root):
                reports[str(path)] = path
    return sorted(reports.values(), key=lambda p: str(p))


def validate_report(path: Path, root: Path) -> list[GuardFinding]:
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[GuardFinding] = []

    if not SOURCE_RE.search(text):
        findings.append(GuardFinding("missing_sources", "research report must include source evidence", rel))
    if not DECISION_RE.search(text):
        findings.append(GuardFinding("missing_decision", "research report must include adoption/rejection rationale", rel))
    has_open_blockers = any(
        match.group(1).strip().lower() not in {"0", "none", "なし", "no", "false"}
        for match in OPEN_BLOCKER_LINE_RE.finditer(text)
    )
    if has_open_blockers or UNCHECKED_BLOCKER_RE.search(text):
        findings.append(GuardFinding("open_blockers", "research report has unresolved blockers", rel))

    return findings


def check_research_gate(root: Path) -> dict[str, object]:
    reports = find_reports(root)
    findings: list[GuardFinding] = []
    if not reports:
        findings.append(
            GuardFinding(
                "missing_research_report",
                "G1R requires a research report under docs/research, .helix/research, or D-RES",
            )
        )

    for report in reports:
        findings.extend(validate_report(report, root))

    return {
        "ok": not findings,
        "reports": [str(path.relative_to(root)) if path.is_relative_to(root) else str(path) for path in reports],
        "errors": [asdict(item) for item in findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="research_guard")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = check_research_gate(Path(args.root).resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        if payload["ok"]:
            print(f"[research-guard] OK: {len(payload['reports'])} research report(s) found")
        else:
            print("[research-guard] FAIL: G1R research evidence is incomplete", file=sys.stderr)
            for item in payload["errors"]:
                path = f" ({item['path']})" if item.get("path") else ""
                print(f"  - {item['code']}: {item['message']}{path}", file=sys.stderr)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
