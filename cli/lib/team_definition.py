from __future__ import annotations

import re
from typing import Any

import yaml_parser


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1]
    return v


def _parse_member_line(line: str) -> tuple[str, str] | None:
    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.+)$", line.strip())
    if match is None:
        return None
    return match.group(1), _strip_quotes(match.group(2))


def parse_team_yaml(text: str) -> dict[str, Any]:
    """チーム定義 YAML の簡易パース。"""

    header_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*members\s*:\s*$", line):
            break
        header_lines.append(line)

    header = yaml_parser.parse_yaml("\n".join(header_lines)) if header_lines else {}
    result: dict[str, Any] = {
        "name": _strip_quotes(str(header.get("name", ""))),
        "strategy": _strip_quotes(str(header.get("strategy", "sequential"))),
        "members": [],
    }

    members: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_members = False

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if re.match(r"^members\s*:\s*$", stripped):
            in_members = True
            continue

        if not in_members:
            continue

        if stripped.startswith("- "):
            if current:
                members.append(current)
            current = {}
            rest = stripped[2:].strip()
            if rest:
                parsed = _parse_member_line(rest)
                if parsed is not None:
                    key, value = parsed
                    current[key] = value
            continue

        if current is None:
            continue

        parsed = _parse_member_line(stripped)
        if parsed is not None:
            key, value = parsed
            current[key] = value

    if current:
        members.append(current)

    result["members"] = [member for member in members if "role" in member]
    return result
