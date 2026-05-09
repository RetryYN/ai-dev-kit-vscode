from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PLAN_NUMBER_RE = re.compile(r"PLAN-(\d{3,})")
STATUS_LINE_RE = re.compile(r"^\s*status:\s*(draft|finalized|completed)\s*$")
PLAN_ID_LINE_RE = re.compile(r"^\s*plan_id:\s*(PLAN-\d{3,})\s*$")
LINT_SELF_REFERENCE_RE = re.compile(r"^\s*lint_self_reference:\s*(true|false)\s*$")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
DATE_LOG_RE = re.compile(r"^\s*\d{4}-\d{2}-\d{2}\b.*\bstatus\s+(draft|finalized|completed)\b")
ASSERTIVE_PATTERNS = (
    re.compile(r"現在の status は (?P<status>draft|finalized|completed)(?: です)?"),
    re.compile(r"(?:本 PLAN の )?status は (?P<status>draft|finalized|completed) です"),
    re.compile(r"(?:本 PLAN の )?status は (?P<status>draft|finalized|completed) として運用中"),
    re.compile(r"status:\s*(?P<status>draft|finalized|completed)\s*として運用(?:中)?"),
)
SKIP_SECTION_KEYWORDS = ("out of scope", "retro placeholder")
SELF_REFERENCE_SECTION_RE = re.compile(r"^§?(?P<section>\d+\.\d+)\s+W-(?P<work_id>\d+)\b")
SECTION_2_1_RE = re.compile(r"^§?2\.1\b")
W_ITEM_RE = re.compile(r"^\s*-\s*W-(?P<work_id>\d+)\b")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*]\s+|\d+[.)]\s+)")
KIND_LINE_RE = re.compile(r"^(?P<kind>影響範囲|DoD|Test Plan|実装方針)\s*[:：]?\s*(?P<rest>.*)$", re.IGNORECASE)
NON_TEXT_RE = re.compile(r"[^0-9A-Za-z\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+")
SELF_REFERENCE_PLAN_NUMBERS = {36, 37}
KIND_NAMES = {
    "影響範囲": "影響範囲",
    "dod": "DoD",
    "test plan": "Test Plan",
    "実装方針": "実装方針",
}
WARN_SIMILARITY = 0.4
HIGHLIGHT_SIMILARITY = 0.7


@dataclass(frozen=True)
class Finding:
    line_no: int
    expected: str
    actual: str
    line_text: str


@dataclass(frozen=True)
class DuplicateCandidate:
    work_id: str
    kind: str
    section_label: str
    line_no: int
    text: str


@dataclass(frozen=True)
class DuplicateWarning:
    work_id: str
    kind: str
    scope_section_label: str
    scope_line_no: int
    sprint_section_label: str
    sprint_line_no: int
    similarity: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="helix plan lint",
        description="Lint PLAN markdown status assertions against frontmatter.status",
    )
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="duplicate-only モードで markdown table を stdout に出力する",
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


def _extract_status(frontmatter_lines: list[str]) -> tuple[str, str | None, bool]:
    status: str | None = None
    plan_id: str | None = None
    lint_self_reference = False

    for line in frontmatter_lines:
        if status is None:
            status_match = STATUS_LINE_RE.match(line)
            if status_match:
                status = status_match.group(1)
        if plan_id is None:
            plan_id_match = PLAN_ID_LINE_RE.match(line)
            if plan_id_match:
                plan_id = plan_id_match.group(1)
        if not lint_self_reference:
            lint_self_reference_match = LINT_SELF_REFERENCE_RE.match(line)
            if lint_self_reference_match:
                lint_self_reference = lint_self_reference_match.group(1) == "true"

    if status is None:
        raise ValueError("frontmatter.status が見つかりません")
    return status, plan_id, lint_self_reference


def _parse_heading(line: str) -> tuple[int, str] | None:
    match = HEADING_RE.match(line)
    if not match:
        return None
    return len(match.group(1)), match.group(2)


def _is_skip_section_heading(heading: str) -> bool:
    heading = heading.lower()
    return any(keyword in heading for keyword in SKIP_SECTION_KEYWORDS)


def _is_self_reference_skip_heading(level: int, heading: str, lint_self_reference: bool) -> bool:
    return lint_self_reference and level == 3 and SELF_REFERENCE_SECTION_RE.match(heading) is not None


def _strip_list_prefix(text: str) -> str:
    return LIST_PREFIX_RE.sub("", text, count=1).strip()


def _normalize_kind(text: str) -> tuple[str, str] | None:
    normalized = _strip_list_prefix(text).replace("**", "").strip()
    match = KIND_LINE_RE.match(normalized)
    if not match:
        return None
    kind_key = match.group("kind").lower()
    kind = KIND_NAMES.get(kind_key)
    if kind is None:
        return None
    return kind, match.group("rest").strip()


def _three_grams(text: str) -> set[str]:
    cleaned = NON_TEXT_RE.sub("", _strip_list_prefix(text))
    if not cleaned:
        return set()
    if len(cleaned) < 3:
        return {cleaned}
    return {cleaned[idx : idx + 3] for idx in range(len(cleaned) - 2)}


def _jaccard_similarity(left: str, right: str) -> float:
    left_grams = _three_grams(left)
    right_grams = _three_grams(right)
    if not left_grams or not right_grams:
        return 0.0
    return len(left_grams & right_grams) / len(left_grams | right_grams)


def _record_duplicate_candidate(
    store: dict[tuple[str, str], list[DuplicateCandidate]],
    work_id: str,
    kind: str,
    section_label: str,
    line_no: int,
    text: str,
) -> None:
    cleaned = _strip_list_prefix(text)
    if not cleaned:
        return
    store.setdefault((work_id, kind), []).append(
        DuplicateCandidate(
            work_id=work_id,
            kind=kind,
            section_label=section_label,
            line_no=line_no,
            text=cleaned,
        )
    )


def _collect_duplicate_candidates(
    lines: list[str],
    body_start_idx: int,
) -> tuple[dict[tuple[str, str], list[DuplicateCandidate]], dict[tuple[str, str], list[DuplicateCandidate]]]:
    scope_candidates: dict[tuple[str, str], list[DuplicateCandidate]] = {}
    sprint_candidates: dict[tuple[str, str], list[DuplicateCandidate]] = {}
    in_section_2_1 = False
    current_scope_work_id: str | None = None
    current_sprint_work_id: str | None = None
    current_sprint_section: str | None = None
    current_kind: str | None = None
    current_kind_indent = -1

    for idx in range(body_start_idx + 1, len(lines)):
        line = lines[idx]
        heading = _parse_heading(line)
        if heading is not None:
            level, heading_text = heading
            if level <= 3:
                current_kind = None
                current_kind_indent = -1
            if level == 3 and SECTION_2_1_RE.match(heading_text):
                in_section_2_1 = True
                current_scope_work_id = None
            elif level <= 3:
                in_section_2_1 = False
                current_scope_work_id = None
            if level == 3:
                sprint_match = SELF_REFERENCE_SECTION_RE.match(heading_text)
                if sprint_match:
                    current_sprint_work_id = sprint_match.group("work_id")
                    current_sprint_section = sprint_match.group("section")
                else:
                    current_sprint_work_id = None
                    current_sprint_section = None
            elif level <= 2:
                current_sprint_work_id = None
                current_sprint_section = None
            continue

        indent = len(line) - len(line.lstrip(" "))
        if in_section_2_1:
            work_match = W_ITEM_RE.match(line)
            if work_match:
                current_scope_work_id = work_match.group("work_id")
                current_kind = None
                current_kind_indent = -1
            work_id = current_scope_work_id
            section_label = "2.1"
            target_store = scope_candidates
        elif current_sprint_work_id is not None and current_sprint_section is not None:
            work_id = current_sprint_work_id
            section_label = current_sprint_section
            target_store = sprint_candidates
        else:
            continue

        if work_id is None:
            continue

        kind_match = _normalize_kind(line)
        if kind_match is not None:
            current_kind, rest = kind_match
            current_kind_indent = indent
            if rest:
                _record_duplicate_candidate(target_store, work_id, current_kind, section_label, idx + 1, rest)
            continue

        if current_kind is None or indent <= current_kind_indent:
            current_kind = None
            current_kind_indent = -1
            continue

        _record_duplicate_candidate(target_store, work_id, current_kind, section_label, idx + 1, line)

    return scope_candidates, sprint_candidates


def _find_duplicate_warnings(lines: list[str], body_start_idx: int) -> list[DuplicateWarning]:
    scope_candidates, sprint_candidates = _collect_duplicate_candidates(lines, body_start_idx)
    warnings: list[DuplicateWarning] = []

    for key, sprint_entries in sprint_candidates.items():
        scope_entries = scope_candidates.get(key)
        if not scope_entries:
            continue
        for sprint_entry in sprint_entries:
            best_scope_entry: DuplicateCandidate | None = None
            best_similarity = 0.0
            for scope_entry in scope_entries:
                similarity = _jaccard_similarity(scope_entry.text, sprint_entry.text)
                if similarity <= best_similarity:
                    continue
                best_similarity = similarity
                best_scope_entry = scope_entry
            if best_similarity < WARN_SIMILARITY:
                continue
            if best_scope_entry is None:
                continue
            warnings.append(
                DuplicateWarning(
                    work_id=sprint_entry.work_id,
                    kind=sprint_entry.kind,
                    scope_section_label=best_scope_entry.section_label,
                    scope_line_no=best_scope_entry.line_no,
                    sprint_section_label=sprint_entry.section_label,
                    sprint_line_no=sprint_entry.line_no,
                    similarity=best_similarity,
                )
            )

    warnings.sort(key=lambda warning: (warning.sprint_line_no, warning.kind))
    return warnings


def _duplicate_level(similarity: float) -> str:
    if similarity >= HIGHLIGHT_SIMILARITY:
        return "highlight"
    return "warn"


def _render_duplicate_report(warnings: list[DuplicateWarning]) -> None:
    print("| section_a | line_a | section_b | line_b | jaccard | level |")
    print("|---|---|---|---|---|---|")
    for warning in warnings:
        print(
            f"| §{warning.scope_section_label} | {warning.scope_line_no} | "
            f"§{warning.sprint_section_label} W-{warning.work_id} | {warning.sprint_line_no} | "
            f"{warning.similarity:.2f} | {_duplicate_level(warning.similarity)} |"
        )


def _find_mismatches(
    lines: list[str],
    body_start_idx: int,
    expected_status: str,
    lint_self_reference: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    skip_section_level: int | None = None
    self_reference_skip_level: int | None = None

    for idx in range(body_start_idx + 1, len(lines)):
        line = lines[idx]

        heading = _parse_heading(line)
        if heading is not None:
            level, heading_text = heading
            if skip_section_level is not None and level <= skip_section_level:
                skip_section_level = None
            if self_reference_skip_level is not None and level <= self_reference_skip_level:
                self_reference_skip_level = None
            if _is_skip_section_heading(heading_text):
                skip_section_level = level
            elif _is_self_reference_skip_heading(level, heading_text, lint_self_reference):
                self_reference_skip_level = level
            continue

        if skip_section_level is not None or self_reference_skip_level is not None or DATE_LOG_RE.match(line):
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


def _lint_plan(path: Path, duplicates_only: bool = False) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print(f"FAIL: plan file が見つかりません: {path}", file=sys.stderr)
        return 1

    try:
        frontmatter_lines, body_start_idx = _extract_frontmatter(lines)
        expected_status, frontmatter_plan_id, lint_self_reference = _extract_status(frontmatter_lines)
    except ValueError as exc:
        print(f"FAIL: {path}: {exc}", file=sys.stderr)
        return 1

    plan_number = _resolve_plan_number(path, frontmatter_plan_id)
    if not duplicates_only and plan_number is not None and plan_number < 36:
        print(f"PASS: lint skipped for PLAN-{plan_number:03d} (retroactive 対象外)")
        return 0

    lint_self_reference = lint_self_reference or plan_number in SELF_REFERENCE_PLAN_NUMBERS
    duplicate_warnings = _find_duplicate_warnings(lines, body_start_idx)
    if duplicates_only:
        _render_duplicate_report(duplicate_warnings)
        return 0

    findings = _find_mismatches(lines, body_start_idx, expected_status, lint_self_reference)

    for warning in duplicate_warnings:
        print(
            f"{path}:{warning.sprint_line_no}: WARN: W-{warning.work_id} '{warning.kind}' "
            f"duplicated with §{warning.sprint_section_label} (similarity={warning.similarity:.2f})",
            file=sys.stderr,
        )

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
    return _lint_plan(Path(args.plan_file), duplicates_only=args.duplicates)


if __name__ == "__main__":
    raise SystemExit(main())
