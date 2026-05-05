#!/usr/bin/env python3
"""PreToolUse guard for WebSearch/WebFetch hook events.

The hard "must research" enforcement lives at G1R via research_guard.py.
This hook makes WebSearch/WebFetch events controllable by HELIX settings and
keeps a fail-close command surface available for stricter project policies.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


ALLOWED_TOOLS = {"WebSearch", "WebFetch"}


def _load_payload() -> dict[str, Any] | None:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("[helix-pre-research] DENY: invalid hook JSON", file=sys.stderr)
        return None
    if not isinstance(payload, dict):
        print("[helix-pre-research] DENY: payload must be a JSON object", file=sys.stderr)
        return None
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="research_tool_guard")
    parser.add_argument("command", nargs="?", default="check-tool")
    args = parser.parse_args(argv)
    if args.command not in {"check-tool", "check"}:
        parser.error("command must be check-tool")

    payload = _load_payload()
    if payload is None:
        return 1
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name and tool_name not in ALLOWED_TOOLS:
        print(f"[helix-pre-research] DENY: unexpected tool for research guard: {tool_name}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
