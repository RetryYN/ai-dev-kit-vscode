#!/usr/bin/env python3
"""HELIX template migration utility.

Subcommands:
- detect
- merge --dry-run|--apply
- rollback
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

TARGETS = {
    "phase.yaml": "phase.yaml",
    "gate-checks.yaml": "gate-checks.yaml",
    "doc-map.yaml": "doc-map.yaml",
    "matrix.yaml": "matrix.yaml",
    "framework.yaml": "framework.yaml",
}

VERSION_RE = re.compile(r"helix_template_version:\s*(\d+)")
BLOCK_STYLE_RE = re.compile(r"\|[+-]?$|>[+-]?$")
FRAMEWORK_TEMPLATE_FALLBACK = """# helix_template_version: 3
detected: unknown
tools: {}
"""


class YamlParseError(ValueError):
    pass


def detect_template_version(text: str) -> int | None:
    m = VERSION_RE.search(text)
    return int(m.group(1)) if m else None


def load_template_text(name: str, template_path: Path) -> tuple[str, bool]:
    if template_path.exists():
        return template_path.read_text(encoding="utf-8"), True
    if name == "framework.yaml":
        return FRAMEWORK_TEMPLATE_FALLBACK, False
    raise FileNotFoundError(str(template_path))


def _strip_comment(value: str) -> str:
    out = []
    in_quote = None
    i = 0
    while i < len(value):
        ch = value[i]
        if in_quote:
            if ch == in_quote:
                in_quote = None
            out.append(ch)
        else:
            if ch in ('"', "'"):
                in_quote = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _unquote(text: str) -> str:
    if len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        return text[1:-1]
    return text


def _parse_scalar(value: str) -> Any:
    v = _strip_comment(value).strip()
    if v == "":
        return ""
    if v in ("null", "Null", "NULL", "~"):
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    if re.fullmatch(r"-?\d+", v):
        try:
            return int(v)
        except ValueError:
            pass
    if v.startswith("{") and v.endswith("}"):
        return _parse_inline_map(v)
    if v.startswith("[") and v.endswith("]"):
        return _parse_inline_list(v)
    return _unquote(v)


def _split_top(s: str, delim: str) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    in_quote = None
    for ch in s:
        if in_quote:
            if ch == in_quote:
                in_quote = None
            cur.append(ch)
            continue
        if ch in ('"', "'"):
            in_quote = ch
            cur.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth = max(0, depth - 1)
        if ch == delim and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    last = "".join(cur).strip()
    if last:
        parts.append(last)
    return parts


def _parse_inline_map(value: str) -> dict[str, Any]:
    body = value[1:-1].strip()
    if not body:
        return {}
    out: dict[str, Any] = {}
    for part in _split_top(body, ","):
        if ":" not in part:
            raise YamlParseError(f"invalid inline map part: {part}")
        k, v = part.split(":", 1)
        out[_unquote(k.strip())] = _parse_scalar(v.strip())
    return out


def _parse_inline_list(value: str) -> list[Any]:
    body = value[1:-1].strip()
    if not body:
        return []
    return [_parse_scalar(p) for p in _split_top(body, ",")]


def load_yaml(text: str) -> Any:
    lines = text.splitlines()
    root: Any = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    i = 0

    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw[indent:]

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            item_text = line[2:].strip()
            if not isinstance(parent, list):
                raise YamlParseError("list item under non-list")
            if ":" in item_text and not item_text.startswith(("\"", "'")):
                k, v = item_text.split(":", 1)
                k = _unquote(k.strip())
                v = v.strip()
                node: dict[str, Any] = {}
                if v == "":
                    node[k] = {}
                    parent.append(node)
                    stack.append((indent + 2, node))
                elif BLOCK_STYLE_RE.fullmatch(v):
                    block, next_i = _collect_block_scalar(lines, i + 1, indent)
                    node[k] = block
                    parent.append(node)
                    stack.append((indent + 2, node))
                    i = next_i
                    continue
                else:
                    node[k] = _parse_scalar(v)
                    parent.append(node)
                    stack.append((indent + 2, node))
            elif item_text == "":
                node = {}
                parent.append(node)
                stack.append((indent + 2, node))
            else:
                parent.append(_parse_scalar(item_text))
            i += 1
            continue

        if ":" not in line:
            raise YamlParseError(f"invalid yaml line: {line}")

        key_raw, value_raw = line.split(":", 1)
        key = _unquote(key_raw.strip())
        value = value_raw.strip()

        if value == "":
            next_obj: Any = {}
            j = i + 1
            while j < len(lines):
                probe = lines[j]
                if not probe.strip() or probe.lstrip().startswith("#"):
                    j += 1
                    continue
                p_indent = len(probe) - len(probe.lstrip(" "))
                p_line = probe[p_indent:]
                if p_indent > indent and p_line.startswith("- "):
                    next_obj = []
                break
            if not isinstance(parent, dict):
                raise YamlParseError("mapping key under non-dict")
            parent[key] = next_obj
            stack.append((indent, next_obj))
            i += 1
            continue

        if BLOCK_STYLE_RE.fullmatch(value):
            block, next_i = _collect_block_scalar(lines, i + 1, indent)
            if not isinstance(parent, dict):
                raise YamlParseError("mapping key under non-dict")
            parent[key] = block
            i = next_i
            continue

        if not isinstance(parent, dict):
            raise YamlParseError("mapping key under non-dict")
        parent[key] = _parse_scalar(value)
        i += 1

    return root


def _collect_block_scalar(lines: list[str], start: int, base_indent: int) -> tuple[str, int]:
    out: list[str] = []
    i = start
    min_indent: int | None = None

    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            out.append("")
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent <= base_indent:
            break
        if min_indent is None or indent < min_indent:
            min_indent = indent
        out.append(raw)
        i += 1

    if min_indent is None:
        return "", i

    trimmed = [ln[min_indent:] if ln else "" for ln in out]
    return "\n".join(trimmed).rstrip("\n") + "\n", i


def _scalar_to_yaml(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        if v == "":
            return '""'
        if any(c in v for c in [":", "#", "{", "}", "[", "]", ","]) or v.strip() != v:
            return json.dumps(v, ensure_ascii=False)
        return v
    return json.dumps(v, ensure_ascii=False)


def dump_yaml(data: Any, indent: int = 0) -> str:
    sp = " " * indent
    lines: list[str] = []

    if isinstance(data, dict):
        for k, v in data.items():
            key = json.dumps(k, ensure_ascii=False) if any(ch in k for ch in [":", " "]) else k
            if isinstance(v, dict):
                lines.append(f"{sp}{key}:")
                lines.append(dump_yaml(v, indent + 2))
            elif isinstance(v, list):
                lines.append(f"{sp}{key}:")
                lines.append(dump_yaml(v, indent + 2))
            elif isinstance(v, str) and "\n" in v:
                lines.append(f"{sp}{key}: |")
                for ln in v.rstrip("\n").split("\n"):
                    lines.append(f"{' ' * (indent + 2)}{ln}")
            else:
                lines.append(f"{sp}{key}: {_scalar_to_yaml(v)}")
        return "\n".join(lines)

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{sp}- {{}}")
                    continue
                first = True
                for k, v in item.items():
                    key = json.dumps(k, ensure_ascii=False) if any(ch in k for ch in [":", " "]) else k
                    prefix = f"{sp}- " if first else f"{' ' * (indent + 2)}"
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}{key}:")
                        lines.append(dump_yaml(v, indent + 4))
                    elif isinstance(v, str) and "\n" in v:
                        lines.append(f"{prefix}{key}: |")
                        for ln in v.rstrip("\n").split("\n"):
                            lines.append(f"{' ' * (indent + 4)}{ln}")
                    else:
                        lines.append(f"{prefix}{key}: {_scalar_to_yaml(v)}")
                    first = False
            elif isinstance(item, list):
                lines.append(f"{sp}-")
                lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{sp}- {_scalar_to_yaml(item)}")
        return "\n".join(lines)

    return f"{sp}{_scalar_to_yaml(data)}"


def deep_merge(template: Any, existing: Any) -> Any:
    if isinstance(template, dict) and isinstance(existing, dict):
        out: dict[str, Any] = {}
        for k, tv in template.items():
            if k in existing:
                out[k] = deep_merge(tv, existing[k])
            else:
                out[k] = tv
        for k, ev in existing.items():
            if k not in out:
                out[k] = ev
        return out
    if isinstance(template, list) and isinstance(existing, list):
        return existing
    return existing


def apply_legacy_mapping(file_kind: str, existing: dict[str, Any]) -> dict[str, Any]:
    if file_kind != "phase.yaml":
        return existing
    if "phase" in existing and "current_phase" not in existing:
        existing["current_phase"] = existing.pop("phase")
    if "sprint_step" in existing:
        sprint = existing.setdefault("sprint", {})
        if isinstance(sprint, dict) and "current_step" not in sprint:
            sprint["current_step"] = existing.pop("sprint_step")
    if "gate" in existing and isinstance(existing["gate"], dict):
        gates = existing.setdefault("gates", {})
        if isinstance(gates, dict):
            for gk, gv in existing.pop("gate").items():
                gates.setdefault(gk, gv)
    return existing


def _merge_doc_map(template: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    merged = deep_merge(template, existing)
    if not isinstance(merged, dict):
        return merged
    t = template.get("triggers") if isinstance(template, dict) else None
    e = existing.get("triggers") if isinstance(existing, dict) else None
    if isinstance(t, list) and isinstance(e, list):
        seen = set()
        out = []
        for item in e:
            if isinstance(item, dict) and "pattern" in item:
                seen.add(item["pattern"])
            out.append(item)
        for item in t:
            if isinstance(item, dict) and item.get("pattern") in seen:
                continue
            out.append(item)
        merged["triggers"] = out
    return merged


def merge_yaml(existing_text: str, template_text: str, file_kind: str) -> str:
    if not existing_text.strip():
        return template_text.rstrip() + "\n"

    head_comments = []
    for ln in existing_text.splitlines():
        if ln.lstrip().startswith("#") or not ln.strip():
            head_comments.append(ln)
            continue
        break

    try:
        existing_obj = load_yaml(existing_text)
        template_obj = load_yaml(template_text)
    except Exception:
        # Conservative fallback: keep existing file if parser cannot handle structure.
        return existing_text if existing_text.endswith("\n") else existing_text + "\n"
    if not isinstance(existing_obj, dict) or not isinstance(template_obj, dict):
        raise YamlParseError("root must be mapping")

    existing_obj = apply_legacy_mapping(file_kind, existing_obj)

    if file_kind == "doc-map.yaml":
        merged = _merge_doc_map(template_obj, existing_obj)
    else:
        merged = deep_merge(template_obj, existing_obj)

    if file_kind == "matrix.yaml" and isinstance(merged, dict):
        if isinstance(existing_obj.get("features"), (list, dict)):
            merged["features"] = existing_obj["features"]
        if isinstance(existing_obj.get("waivers"), (list, dict)):
            merged["waivers"] = existing_obj["waivers"]

    if file_kind == "framework.yaml" and isinstance(merged, dict):
        if "detected" not in merged:
            merged["detected"] = "unknown"
        if "tools" not in merged or not isinstance(merged.get("tools"), dict):
            merged["tools"] = {}

    body = dump_yaml(merged).rstrip() + "\n"
    if head_comments:
        return "\n".join(head_comments).rstrip() + "\n" + body
    return body


def create_backup(helix_dir: Path) -> Path:
    backup_root = helix_dir / "backup"
    backup_root.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / ts
    suffix = 1
    while backup_dir.exists():
        backup_dir = backup_root / f"{ts}-{suffix}"
        suffix += 1
    backup_dir.mkdir(parents=True, exist_ok=False)

    for name in TARGETS:
        src = helix_dir / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
    return backup_dir


def prune_backups(helix_dir: Path, keep: int = 5) -> None:
    backup_root = helix_dir / "backup"
    if not backup_root.exists():
        return
    dirs = sorted([p for p in backup_root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    for old in dirs[keep:]:
        shutil.rmtree(old, ignore_errors=True)


def rollback(helix_dir: Path) -> Path:
    backup_root = helix_dir / "backup"
    if not backup_root.exists():
        raise FileNotFoundError("backup directory not found")
    dirs = sorted([p for p in backup_root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    if not dirs:
        raise FileNotFoundError("no backup snapshots")
    latest = dirs[0]
    restored = 0
    for name in TARGETS:
        src = latest / name
        if src.exists():
            shutil.copy2(src, helix_dir / name)
            restored += 1
    if restored == 0:
        raise RuntimeError("latest backup has no target files")
    return latest


def detect(helix_dir: Path, templates_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, tpl in TARGETS.items():
        current_path = helix_dir / name
        template_path = templates_dir / tpl
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else ""
        try:
            template_text, template_exists = load_template_text(name, template_path)
        except FileNotFoundError:
            template_text, template_exists = "", False
        result[name] = {
            "path": str(current_path),
            "template": str(template_path),
            "current_version": detect_template_version(current_text),
            "latest_version": detect_template_version(template_text),
            "exists": current_path.exists(),
            "template_exists": template_exists,
        }
    return result


def do_merge(helix_dir: Path, templates_dir: Path, apply: bool) -> int:
    changes = []
    for name, tpl in TARGETS.items():
        current_path = helix_dir / name
        template_path = templates_dir / tpl
        try:
            template_text, _ = load_template_text(name, template_path)
        except FileNotFoundError:
            print(f"template not found: {template_path}", file=sys.stderr)
            return 2
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else ""

        current_v = detect_template_version(current_text)
        latest_v = detect_template_version(template_text)
        if current_v is not None and latest_v is not None and current_v == latest_v:
            continue

        try:
            merged_text = merge_yaml(current_text, template_text, name)
        except Exception as e:
            print(f"merge failed for {name}: {e}", file=sys.stderr)
            return 1

        if merged_text != current_text:
            diff = difflib.unified_diff(
                current_text.splitlines(keepends=True),
                merged_text.splitlines(keepends=True),
                fromfile=str(current_path),
                tofile=f"{current_path} (merged)",
            )
            changes.append((name, current_path, merged_text, "".join(diff)))

    if not changes:
        print("no changes")
        return 0

    for name, _, _, diff_text in changes:
        print(f"[{name}]")
        print(diff_text.rstrip())

    if not apply:
        return 0

    backup = create_backup(helix_dir)
    for _, path, merged_text, _ in changes:
        path.write_text(merged_text, encoding="utf-8")
    prune_backups(helix_dir, keep=5)
    print(f"Backup: {backup}")
    print("Done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Migrate .helix yaml files to latest templates")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--helix-dir", type=Path, required=True, help="path to .helix directory")
    common.add_argument("--templates-dir", type=Path, required=True, help="path to templates directory")

    sub.add_parser("detect", parents=[common], help="show current/latest versions as JSON")

    merge = sub.add_parser("merge", parents=[common], help="merge with diff output")
    mg = merge.add_mutually_exclusive_group(required=True)
    mg.add_argument("--dry-run", action="store_true", help="show diff only")
    mg.add_argument("--apply", action="store_true", help="write merged files")

    sub.add_parser("rollback", parents=[common], help="restore from latest backup")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    helix_dir: Path = args.helix_dir
    templates_dir: Path = args.templates_dir

    if not helix_dir.exists():
        print(f"helix dir not found: {helix_dir}", file=sys.stderr)
        return 2

    if args.command == "detect":
        data = detect(helix_dir, templates_dir)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if args.command == "merge":
        return do_merge(helix_dir, templates_dir, apply=args.apply)

    if args.command == "rollback":
        try:
            latest = rollback(helix_dir)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            return 3
        except Exception as e:
            print(f"rollback failed: {e}", file=sys.stderr)
            return 1
        print(f"Restored from {latest}")
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
