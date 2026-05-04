#!/usr/bin/env python3
"""Claude Code hook payload helpers."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from typing import Any


SAFE_HOOK_PATH_RE = re.compile(
    r"^[A-Za-z0-9/_.\-\u3000-\u303F\u3040-\u30FF\u3400-\u4DBF"
    r"\u4E00-\u9FFF\uF900-\uFAFF\uFF01-\uFF60\uFFE0-\uFFEE]+$"
)

PATH_KEYS = ("file_path", "filePath", "path")
PATH_LIST_KEYS = ("file_paths", "filePaths", "paths", "files")


def is_safe_hook_path(path: str) -> bool:
    return bool(path and SAFE_HOOK_PATH_RE.fullmatch(path))


def _iter_path_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return

    if isinstance(value, list):
        for item in value:
            yield from _iter_path_values(item)
        return

    if isinstance(value, dict):
        for key in PATH_KEYS:
            candidate = value.get(key)
            if isinstance(candidate, str):
                yield candidate
        return


def candidate_paths(payload: dict[str, Any]) -> list[str]:
    """Return path candidates from known Claude Code hook payload sections."""

    values: list[str] = []
    for section_name in ("tool_input", "tool_response"):
        section = payload.get(section_name)
        if not isinstance(section, dict):
            continue

        for key in PATH_KEYS:
            candidate = section.get(key)
            if isinstance(candidate, str):
                values.append(candidate)

        for key in PATH_LIST_KEYS:
            values.extend(_iter_path_values(section.get(key)))

    return values


def extract_changed_paths(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return unique safe paths and rejected unsafe candidates."""

    safe_paths: list[str] = []
    rejected: list[str] = []
    seen: set[str] = set()

    for path in candidate_paths(payload):
        if path in seen:
            continue
        seen.add(path)
        if is_safe_hook_path(path):
            safe_paths.append(path)
        else:
            rejected.append(path)

    return safe_paths, rejected


def _load_payload(stream: Any) -> dict[str, Any]:
    raw = stream.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[helix-post-tool-use] WARN: invalid hook JSON skipped: {exc}", file=sys.stderr)
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "paths"
    if command in ("--help", "-h"):
        print("Usage: hook_payload.py paths")
        return 0
    if command != "paths":
        print("Usage: hook_payload.py paths", file=sys.stderr)
        return 2

    safe_paths, rejected = extract_changed_paths(_load_payload(sys.stdin))
    for path in rejected:
        print(f"[helix-post-tool-use] WARN: unsupported file_path skipped: {path!r}", file=sys.stderr)
    for path in safe_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
