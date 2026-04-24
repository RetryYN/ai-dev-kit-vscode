#!/usr/bin/env python3
"""スキル catalog の生成・保存・検索を行う。"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .command_mapper import derive_commands
    from .skill_jsonl_schema import JsonlSchemaError, compute_source_hash, validate_entry
except ImportError:  # pragma: no cover - script execution fallback
    from command_mapper import derive_commands
    from skill_jsonl_schema import JsonlSchemaError, compute_source_hash, validate_entry


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
    return _normalize_frontmatter(parsed)


def _normalize_frontmatter(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    current_metadata = normalized.get("metadata")
    metadata = dict(current_metadata) if isinstance(current_metadata, dict) else {}

    for key in ("helix_layer", "helix_gate", "triggers", "verification"):
        if key in normalized and key not in metadata:
            metadata[key] = _normalize_frontmatter_value(normalized[key])

    if metadata:
        normalized["metadata"] = metadata
    return normalized


def _normalize_frontmatter_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not (text.startswith("[") and text.endswith("]")):
        return value

    inner = text[1:-1].strip()
    if not inner:
        return []
    return [_parse_scalar(part.strip()) for part in inner.split(",")]


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
    skill_id = f"{category}/{name}"
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
        "id": skill_id,
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
        "commands": derive_commands({"metadata": metadata, "id": skill_id, "helix_layer": metadata.get("helix_layer")}),
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
    tmp_path = cache_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, cache_path)


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


_ALL_FORWARD_PHASES = ("L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8")
_MAX_REFERENCES_PER_ENTRY = 10
_PHASE_ALIASES = {"S0": "L1", "S1": "L2", "S2": "L4", "S3": "L6", "S4": "L8"}


def _to_phase_list(raw: Any) -> list[str]:
    phases: list[str] = []

    def _append(value: Any) -> None:
        if value is None:
            return
        text = str(value).strip()
        if not text:
            return
        for part in re.split(r"[,/\-]", text):
            phase = _PHASE_ALIASES.get(part.strip(), part.strip())
            if phase == "all":
                for p in _ALL_FORWARD_PHASES:
                    if p not in phases:
                        phases.append(p)
            elif phase and phase not in phases:
                phases.append(phase)

    if isinstance(raw, list):
        for item in raw:
            _append(item)
    else:
        _append(raw)
    return phases


def _to_summary(description: Any) -> str:
    text = str(description or "").strip()
    if len(text) <= 30:
        return text
    return f"{text[:30]}..."


def _default_agent(skill_id: str, category: str, phases: list[str]) -> str:
    if skill_id == "common/security":
        return "security"
    if skill_id == "common/testing":
        return "qa"
    if category == "workflow" or any(phase in {"L2", "L3"} for phase in phases):
        return "tl"
    return "pg"


def _classification_for_entry(existing: dict[str, Any] | None, new_hash: str) -> dict[str, Any]:
    if not isinstance(existing, dict):
        return {"status": "pending", "classified_at": None, "classifier_model": None}

    existing_hash = existing.get("source_hash")
    existing_class = existing.get("classification")
    if not isinstance(existing_class, dict):
        return {"status": "pending", "classified_at": None, "classifier_model": None}

    status = existing_class.get("status")
    hash_matches = existing_hash == new_hash

    if hash_matches and status in {"approved", "manual"}:
        return dict(existing_class)

    if not hash_matches and status == "manual":
        downgraded = {
            "status": "pending",
            "classified_at": existing_class.get("classified_at"),
            "classifier_model": existing_class.get("classifier_model"),
        }
        if "confidence" in existing_class:
            downgraded["confidence"] = existing_class.get("confidence")
        return downgraded

    return {"status": "pending", "classified_at": None, "classifier_model": None}


def _build_jsonl_entry(skill_md: Path, skills_root: Path, existing_map: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    content = skill_md.read_text(encoding="utf-8")
    frontmatter = _extract_frontmatter(content)
    if not frontmatter:
        _warn(f"frontmatter が無いため JSONL スキップ: {skill_md}")
        return None

    rel = skill_md.relative_to(skills_root)
    parts = rel.parts
    if len(parts) < 3:
        _warn(f"期待するパス構造(category/name/SKILL.md)ではないため JSONL スキップ: {skill_md}")
        return None

    category = parts[0]
    name = parts[1]
    skill_id = f"{category}/{name}"
    metadata = frontmatter.get("metadata", {}) if isinstance(frontmatter.get("metadata"), dict) else {}
    phases = _to_phase_list(metadata.get("helix_layer"))

    references: list[dict[str, str]] = []
    references_dir = skill_md.parent / "references"
    if references_dir.is_dir():
        all_refs = sorted(references_dir.rglob("*.md"))
        priority: list[Path] = []
        normal: list[Path] = []
        for ref in all_refs:
            ref_rel = ref.relative_to(references_dir).as_posix()
            if "brands-" in ref_rel:
                normal.append(ref)
            elif ref.stem.upper() == "INDEX":
                priority.append(ref)
            else:
                priority.append(ref)
        for ref in (priority + normal)[:_MAX_REFERENCES_PER_ENTRY]:
            ref_rel = ref.relative_to(references_dir).as_posix()
            references.append(
                {
                    "path": f"skills/{skill_id}/references/{ref_rel}",
                    "title": ref.stem,
                }
            )

    new_hash = compute_source_hash(content)
    existing = existing_map.get(skill_id)

    if (
        existing is not None
        and existing.get("source_hash") == new_hash
        and isinstance(existing.get("classification"), dict)
        and existing["classification"].get("status") in ("approved", "manual")
    ):
        refreshed = dict(existing)
        refreshed["commands"] = derive_commands(
            {
                "metadata": metadata,
                "id": skill_id,
                "helix_layer": metadata.get("helix_layer"),
            }
        )
        return refreshed

    title = frontmatter.get("name") or frontmatter.get("title") or skill_id
    triggers = metadata.get("triggers", [])
    if not isinstance(triggers, list):
        triggers = []

    return {
        "id": skill_id,
        "title": str(title),
        "summary": _to_summary(frontmatter.get("description")),
        "phases": phases,
        "tasks": [],
        "triggers": [str(item) for item in triggers],
        "anti_triggers": [],
        "agent": _default_agent(skill_id, category, phases),
        "similar": [],
        "commands": derive_commands({"metadata": metadata, "id": skill_id, "helix_layer": metadata.get("helix_layer")}),
        "references": references,
        "source_hash": new_hash,
        "classification": _classification_for_entry(existing, new_hash),
    }


def build_jsonl_catalog(
    skills_root: Path,
    *,
    task_ids: set[str] | None = None,
    existing_jsonl_path: Path | None = None,
) -> list[dict]:
    del task_ids  # classifier 適用前の skeleton 生成では未使用

    resolved_root = skills_root.resolve()
    existing_map: dict[str, dict[str, Any]] = {}
    if existing_jsonl_path is not None:
        for entry in read_jsonl_catalog(existing_jsonl_path):
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                existing_map[entry["id"]] = entry

    entries: list[dict[str, Any]] = []
    for skill_md in sorted(resolved_root.rglob("SKILL.md")):
        entry = _build_jsonl_entry(skill_md, resolved_root, existing_map)
        if entry is not None:
            entries.append(entry)

    return sorted(entries, key=lambda item: str(item.get("id", "")))


def write_jsonl_catalog(entries: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as fp:
        for entry in sorted(entries, key=lambda item: str(item.get("id", ""))):
            try:
                validate_entry(entry, known_task_ids=None)
            except JsonlSchemaError as exc:
                _warn(f"JSONL entry をスキップ: {exc}")
                continue
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_jsonl_catalog(path: Path) -> list[dict]:
    if not path.is_file():
        return []

    entries: list[dict] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        text = raw.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            _warn(f"JSONL parse 失敗 line={line_no}: {exc}")
            continue
        if not isinstance(parsed, dict):
            _warn(f"JSONL parse 失敗 line={line_no}: object ではありません")
            continue
        entries.append(parsed)
    return entries


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
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7
    raise SystemExit(main(sys.argv))
