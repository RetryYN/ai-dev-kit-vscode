#!/usr/bin/env python3
"""doc-map.yaml のトリガーマッチャー。

責務: 変更ファイルに対して doc-map のトリガー種別を判定し、hook 用イベントへ変換する。

Usage:
  python3 doc_map_matcher.py <doc_map_path> <file_path>

出力:
  GATE_READY|<gate>|<file_path>
  DESIGN_SYNC|<design_ref>|<file_path>
  COVERAGE_CHECK|<file_path>
  ADR_INDEX|<file_path>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return text[1:-1]
    return text


def _glob_match(file_path: str, pattern: str) -> bool:
    escaped = re.escape(pattern)
    escaped = escaped.replace(r"\*\*", "__DOUBLE_STAR__")
    escaped = escaped.replace(r"\*", "[^/]*")
    escaped = escaped.replace("__DOUBLE_STAR__", ".*")
    return bool(re.match(f"^{escaped}$", file_path))


def _parse_doc_map(doc_map_path: Path) -> list[dict[str, str]]:
    triggers: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    with doc_map_path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match_pattern = re.match(r"^\s*-\s*pattern:\s*(.+?)\s*$", line)
            if match_pattern:
                if current:
                    triggers.append(current)
                current = {"pattern": _strip_quotes(match_pattern.group(1))}
                continue

            if current is None:
                continue

            for key in ("phase", "on_write", "gate", "design_ref"):
                match_key = re.match(rf"^\s*{key}:\s*(.+?)\s*$", line)
                if match_key:
                    current[key] = _strip_quotes(match_key.group(1))
                    break

    if current:
        triggers.append(current)
    return triggers


def _emit_matches(triggers: list[dict[str, str]], file_path: str) -> None:
    for trigger in triggers:
        pattern = trigger.get("pattern", "")
        if not pattern or not _glob_match(file_path, pattern):
            continue

        on_write = trigger.get("on_write", "")
        gate = trigger.get("gate", "")
        design_ref = trigger.get("design_ref", "")

        if on_write == "gate_ready" and gate:
            print(f"GATE_READY|{gate}|{file_path}")
        elif on_write == "design_sync" and design_ref:
            print(f"DESIGN_SYNC|{design_ref}|{file_path}")
        elif on_write == "coverage_check":
            print(f"COVERAGE_CHECK|{file_path}")
        elif on_write == "adr_index":
            print(f"ADR_INDEX|{file_path}")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: doc_map_matcher.py <doc_map_path> <file_path>", file=sys.stderr)
        return 1

    doc_map_path = Path(sys.argv[1])
    file_path = sys.argv[2]

    if not doc_map_path.is_file():
        return 0

    try:
        triggers = _parse_doc_map(doc_map_path)
    except OSError:
        return 1

    _emit_matches(triggers, file_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
