from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PLAN_NUMBER_RE = re.compile(r"PLAN-(\d{3,})")
STATUS_LINE_RE = re.compile(r"^\s*status:\s*(draft|finalized|completed)\s*$")
PLAN_ID_LINE_RE = re.compile(r"^\s*plan_id:\s*(PLAN-\d{3,})\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
DATE_LOG_RE = re.compile(r"^\s*\d{4}-\d{2}-\d{2}\b.*\bstatus\s+(draft|finalized|completed)\b")
ASSERTIVE_PATTERNS = (
    re.compile(r"現在の status は (?P<status>draft|finalized|completed)(?: です)?"),
    re.compile(r"(?:本 PLAN の )?status は (?P<status>draft|finalized|completed) です"),
    re.compile(r"(?:本 PLAN の )?status は (?P<status>draft|finalized|completed) として運用中"),
    re.compile(r"status:\s*(?P<status>draft|finalized|completed)\s*として運用(?:中)?"),
)
SKIP_SECTION_KEYWORDS = ("out of scope", "retro placeholder")


@dataclass(frozen=True)
class Finding:
    line_no: int
    expected: str
    actual: str
    line_text: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="helix plan lint",
        description="Lint PLAN markdown status assertions against frontmatter.status",
    )
    parser.add_argument("plan_file", help="PLAN markdown file")
    return parser.parse_args()


def _resolve_plan_number(path: Path, frontmatter_plan_id: str | None) -> int | None:
    candidate = frontmatter_plan_id or path.stem
    match = PLAN_NUMBER_RE.search(candidate)
    if not match:
        return None
    return int(match.group(1))


def _extract_frontmatter(lines: list[str]) -> tuple[list[str], int]:
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter がありません")

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return lines[1:idx], idx

    raise ValueError("frontmatter の終端 `---` がありません")


def _extract_status(frontmatter_lines: list[str]) -> tuple[str, str | None]:
    status: str | None = None
    plan_id: str | None = None

    for line in frontmatter_lines:
        if status is None:
            status_match = STATUS_LINE_RE.match(line)
            if status_match:
                status = status_match.group(1)
        if plan_id is None:
            plan_id_match = PLAN_ID_LINE_RE.match(line)
            if plan_id_match:
                plan_id = plan_id_match.group(1)

    if status is None:
        raise ValueError("frontmatter.status が見つかりません")
    return status, plan_id


def _is_skip_section_heading(line: str) -> bool:
    match = HEADING_RE.match(line)
    if not match:
        return False
    heading = match.group(1).lower()
    return any(keyword in heading for keyword in SKIP_SECTION_KEYWORDS)


def _find_mismatches(lines: list[str], body_start_idx: int, expected_status: str) -> list[Finding]:
    findings: list[Finding] = []
    skip_section = False

    for idx in range(body_start_idx + 1, len(lines)):
        line = lines[idx]

        heading_match = HEADING_RE.match(line)
        if heading_match:
            skip_section = _is_skip_section_heading(line)
            continue

        if skip_section or DATE_LOG_RE.match(line):
            continue

        for pattern in ASSERTIVE_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            actual = match.group("status")
            if actual == expected_status:
                break
            findings.append(
                Finding(
                    line_no=idx + 1,
                    expected=expected_status,
                    actual=actual,
                    line_text=line.rstrip(),
                )
            )
            break

    return findings


def _lint_plan(path: Path) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print(f"FAIL: plan file が見つかりません: {path}", file=sys.stderr)
        return 1

    try:
        frontmatter_lines, body_start_idx = _extract_frontmatter(lines)
        expected_status, frontmatter_plan_id = _extract_status(frontmatter_lines)
    except ValueError as exc:
        print(f"FAIL: {path}: {exc}", file=sys.stderr)
        return 1

    plan_number = _resolve_plan_number(path, frontmatter_plan_id)
    if plan_number is not None and plan_number < 36:
        print(f"PASS: lint skipped for PLAN-{plan_number:03d} (retroactive 対象外)")
        return 0
    if plan_number == 36:
        print("PASS: lint skipped for PLAN-036 (self-reference)")
        return 0

    findings = _find_mismatches(lines, body_start_idx, expected_status)
    if not findings:
        print(f"PASS: no contradictory status assertions in {path}")
        return 0

    for finding in findings:
        print(
            f"{path}:{finding.line_no}: frontmatter.status={finding.expected} "
            f"but body asserts {finding.actual}",
            file=sys.stderr,
        )
        print(f"  {finding.line_text}", file=sys.stderr)
    return 1


def main() -> int:
    args = _parse_args()
    return _lint_plan(Path(args.plan_file))


if __name__ == "__main__":
    raise SystemExit(main())
