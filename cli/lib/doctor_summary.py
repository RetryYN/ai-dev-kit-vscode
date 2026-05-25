from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass


RESULT_RE = re.compile(r"結果:\s+(\d+)\s+pass,\s+(\d+)\s+fail,\s+(\d+)\s+warn")
SECTION_RE = re.compile(r"^\[(.+)\]$")
ITEM_RE = re.compile(r"^\s*(✓|△|✗|⚠|WARN:)\s+(.+?)\s*$")
COMPOSITE_COUNT_RE = re.compile(r"(critical|warning|info):\s*(\d+)")
WARNINGS_COUNT_RE = re.compile(r"warnings?:\s*(\d+)")
ROWS_COUNT_RE = re.compile(r"rows?:\s*(\d+)")
KEYED_COUNT_RE = re.compile(r":\s*(\d+)\b")
LEADING_COUNT_RE = re.compile(r"^\s*(\d+)\b")

STATUS_BY_MARKER = {
    "✓": "pass",
    "△": "warn",
    "✗": "fail",
    "⚠": "warn",
    "WARN:": "warn",
}
STATUS_RANK = {"pass": 0, "warn": 1, "fail": 2}


@dataclass
class _PendingIssue:
    status: str
    count: int


def _count_from_text(text: str) -> int:
    composite = [int(value) for _label, value in COMPOSITE_COUNT_RE.findall(text)]
    if composite:
        return sum(composite)

    warning_match = WARNINGS_COUNT_RE.search(text)
    if warning_match:
        return int(warning_match.group(1))

    rows_match = ROWS_COUNT_RE.search(text)
    if rows_match:
        return int(rows_match.group(1))

    keyed_match = KEYED_COUNT_RE.search(text)
    if keyed_match:
        return int(keyed_match.group(1))

    leading_match = LEADING_COUNT_RE.match(text)
    if leading_match:
        return int(leading_match.group(1))

    return 0


def parse_doctor_output(output: str) -> dict[str, object]:
    pass_count = 0
    fail_count = 0
    warn_count = 0
    summary_match = RESULT_RE.search(output)
    if summary_match:
        pass_count, fail_count, warn_count = (int(value) for value in summary_match.groups())

    sections: list[dict[str, object]] = []
    current_section: dict[str, object] | None = None
    current_issue: _PendingIssue | None = None

    def flush_issue() -> None:
        nonlocal current_issue
        if current_section is None or current_issue is None:
            current_issue = None
            return
        if current_issue.status != "pass":
            current_section["count"] = int(current_section["count"]) + (current_issue.count or 1)
        current_issue = None

    def flush_section() -> None:
        nonlocal current_section
        if current_section is None:
            return
        flush_issue()
        if current_section["status"] is None:
            current_section["status"] = "pass"
        sections.append(
            {
                "name": current_section["name"],
                "status": current_section["status"],
                "count": current_section["count"],
            }
        )
        current_section = None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        section_match = SECTION_RE.match(line)
        if section_match:
            flush_section()
            current_section = {"name": section_match.group(1), "status": None, "count": 0}
            continue

        if current_section is None:
            continue

        item_match = ITEM_RE.match(raw_line)
        if item_match:
            flush_issue()
            marker, text = item_match.groups()
            status = STATUS_BY_MARKER[marker]
            section_status = current_section["status"]
            if section_status is None or STATUS_RANK[status] > STATUS_RANK[str(section_status)]:
                current_section["status"] = status
            current_issue = _PendingIssue(status=status, count=_count_from_text(text))
            continue

        if current_issue is not None and raw_line.startswith("    "):
            current_issue.count = max(current_issue.count, _count_from_text(line))
            continue

        flush_issue()

    flush_section()

    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "sections": sections,
    }


def main() -> int:
    payload = parse_doctor_output(sys.stdin.read())
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
