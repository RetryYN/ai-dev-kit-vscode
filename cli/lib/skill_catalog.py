#!/usr/bin/env python3
"""スキル catalog の生成・保存・検索を行う。"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _warn(message: str) -> None:
    print(f"[skill_catalog] 警告: {message}", file=sys.stderr)


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        return text[1:-1]
    return text


def _parse_scalar(value: str) -> Any:
    text = _strip_quotes(value.strip())
    if text == "":
        return ""
    lower = text.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "none", "~"):
        return None
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except ValueError:
            pass
    return text


def _next_non_empty(lines: list[str], start: int) -> tuple[int, str] | None:
    idx = start
    while idx < len(lines):
        line = lines[idx]
        if line.strip() != "":
            return idx, line
        idx += 1
    return None


def _parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    i = index
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if current_indent < indent or not stripped.startswith("- "):
            break
        items.append(_parse_scalar(stripped[2:].strip()))
        i += 1
    return items, i


def _parse_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    i = index
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"frontmatter のインデントが不正です: {line}")

        stripped = line.strip()
        if stripped.startswith("- "):
            raise ValueError(f"frontmatter の構文が不正です: {line}")

        if ":" not in stripped:
            raise ValueError(f"frontmatter の key:value が不正です: {line}")

        key, rest = stripped.split(":", 1)
        key = key.strip()
        value = rest.strip()

        if value:
            result[key] = _parse_scalar(value)
            i += 1
            continue

        nxt = _next_non_empty(lines, i + 1)
        if not nxt:
            result[key] = {}
            i += 1
            continue

        next_idx, next_line = nxt
        next_indent = len(next_line) - len(next_line.lstrip(" "))
        if next_indent <= indent:
            result[key] = {}
            i += 1
            continue

        if next_line.strip().startswith("- "):
            parsed_list, new_i = _parse_list(lines, next_idx, next_indent)
            result[key] = parsed_list
            i = new_i
        else:
            parsed_map, new_i = _parse_mapping(lines, next_idx, next_indent)
            result[key] = parsed_map
            i = new_i
    return result, i


def _extract_frontmatter(text: str) -> dict[str, Any] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break

    if end is None:
        return None

    frontmatter_lines = lines[1:end]
    parsed, _ = _parse_mapping(frontmatter_lines, 0, 0)
    return parsed


def _extract_reference_intro(text: str) -> str:
    intro_lines: list[str] = []
    capturing = False

    for raw in text.splitlines():
        stripped = raw.lstrip()

        if not capturing:
            if stripped.startswith("> 目的:") or stripped.startswith("> ") or stripped == ">":
                capturing = True
            else:
                continue

        if stripped.startswith(">"):
            body = stripped[1:].strip()
            if body.startswith("目的:"):
                body = body[len("目的:") :].strip()
            if body:
                intro_lines.append(body)
            continue

        break

    return " ".join(intro_lines)


def _extract_reference_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _build_skill_entry(skill_md: Path, skills_root: Path) -> dict[str, Any] | None:
    content = skill_md.read_text(encoding="utf-8")
    frontmatter = _extract_frontmatter(content)
    if not frontmatter:
        _warn(f"frontmatter が無いためスキップ: {skill_md}")
        return None

    rel = skill_md.relative_to(skills_root)
    parts = rel.parts
    if len(parts) < 3:
        _warn(f"期待するパス構造(category/name/SKILL.md)ではないためスキップ: {skill_md}")
        return None

    category = parts[0]
    name = parts[1]
    metadata = frontmatter.get("metadata", {}) if isinstance(frontmatter.get("metadata"), dict) else {}
    compatibility = frontmatter.get("compatibility", {}) if isinstance(frontmatter.get("compatibility"), dict) else {}

    references: list[dict[str, str]] = []
    references_dir = skill_md.parent / "references"
    if references_dir.is_dir():
        for ref in sorted(references_dir.rglob("*.md")):
            ref_text = ref.read_text(encoding="utf-8")
            ref_rel = ref.relative_to(skill_md.parent).as_posix()
            references.append(
                {
                    "path": ref_rel,
                    "title": _extract_reference_title(ref_text, ref.stem),
                    "intro": _extract_reference_intro(ref_text),
                }
            )

    return {
        "id": f"{category}/{name}",
        "name": name,
        "category": category,
        "path": f"skills/{rel.as_posix()}",
        "description": str(frontmatter.get("description", "")),
        "helix_layer": str(metadata.get("helix_layer", "")),
        "triggers": metadata.get("triggers", []) if isinstance(metadata.get("triggers"), list) else [],
        "verification": metadata.get("verification", []) if isinstance(metadata.get("verification"), list) else [],
        "compatibility": {
            "claude": bool(compatibility.get("claude", False)),
            "codex": bool(compatibility.get("codex", False)),
        },
        "references": references,
    }


def build_catalog(skills_root: Path) -> dict[str, Any]:
    skills_root = skills_root.resolve()
    skills = []

    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        entry = _build_skill_entry(skill_md, skills_root)
        if entry is not None:
            skills.append(entry)

    reference_count = sum(len(skill["references"]) for skill in skills)
    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_count": len(skills),
        "reference_count": reference_count,
        "skills": skills,
    }


def save_catalog(catalog: dict[str, Any], cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_catalog(cache_path: Path) -> dict[str, Any]:
    return json.loads(cache_path.read_text(encoding="utf-8"))


def find_skill(catalog: dict[str, Any], skill_id: str) -> dict[str, Any] | None:
    target = skill_id.strip()
    if not target:
        return None
    for skill in catalog.get("skills", []):
        if skill.get("id") == target:
            return skill
    for skill in catalog.get("skills", []):
        if skill.get("name") == target:
            return skill
    return None


def _usage() -> None:
    print("Usage:")
    print("  skill_catalog.py build <skills_root> [cache_path]")
    print("  skill_catalog.py load <cache_path>")
    print("  skill_catalog.py find <cache_path> <skill_id>")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        _usage()
        return 64

    cmd = argv[1]

    if cmd == "build":
        if len(argv) not in (3, 4):
            _usage()
            return 64
        skills_root = Path(argv[2])
        catalog = build_catalog(skills_root)
        if len(argv) == 4:
            save_catalog(catalog, Path(argv[3]))
        print(json.dumps(catalog, ensure_ascii=False, indent=2))
        return 0

    if cmd == "load":
        if len(argv) != 3:
            _usage()
            return 64
        catalog = load_catalog(Path(argv[2]))
        print(json.dumps(catalog, ensure_ascii=False, indent=2))
        return 0

    if cmd == "find":
        if len(argv) != 4:
            _usage()
            return 64
        catalog = load_catalog(Path(argv[2]))
        skill = find_skill(catalog, argv[3])
        if skill is None:
            return 1
        print(json.dumps(skill, ensure_ascii=False, indent=2))
        return 0

    _usage()
    return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
