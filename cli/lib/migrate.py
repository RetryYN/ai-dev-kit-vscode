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

from yaml_parser import dump_yaml, parse_yaml
try:
    import yaml as _pyyaml
except Exception:  # pragma: no cover - optional dependency
    _pyyaml = None

TARGETS = {
    "phase.yaml": "phase.yaml",
    "gate-checks.yaml": "gate-checks.yaml",
    "doc-map.yaml": "doc-map.yaml",
    "matrix.yaml": "matrix.yaml",
    "framework.yaml": "framework.yaml",
}

VERSION_RE = re.compile(r"helix_template_version:\s*(\d+)")
FRAMEWORK_TEMPLATE_FALLBACK = """# helix_template_version: 3
detected: unknown
tools: {}
"""


class YamlParseError(ValueError):
    pass


def _load_yaml_legacy(text: str) -> dict[str, Any]:
    """複雑 YAML 向けの互換ローダー（migrate.py 内部専用）。"""
    if _pyyaml is None:
        raise YamlParseError("complex YAML merge is unavailable (PyYAML not installed)")
    loaded = _pyyaml.safe_load(text)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise YamlParseError("root must be mapping")
    return loaded


def _dump_yaml_legacy(data: dict[str, Any]) -> str:
    """複雑 YAML 向けの互換ダンパー（migrate.py 内部専用）。"""
    if _pyyaml is None:
        raise YamlParseError("complex YAML dump is unavailable (PyYAML not installed)")
    return (
        _pyyaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).rstrip()
        + "\n"
    )


def detect_template_version(text: str) -> int | None:
    m = VERSION_RE.search(text)
    return int(m.group(1)) if m else None


def load_template_text(name: str, template_path: Path) -> tuple[str, bool]:
    if template_path.exists():
        return template_path.read_text(encoding="utf-8"), True
    if name == "framework.yaml":
        return FRAMEWORK_TEMPLATE_FALLBACK, False
    raise FileNotFoundError(str(template_path))


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
    def _normalize_sprint_step(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, float):
            text = f"{value}"
            if text.startswith("0."):
                return f".{text[2:]}"
            return text
        if isinstance(value, int):
            return str(value)
        return str(value)

    if "phase" in existing and "current_phase" not in existing:
        existing["current_phase"] = existing.pop("phase")
    if "sprint_step" in existing:
        sprint = existing.setdefault("sprint", {})
        if isinstance(sprint, dict) and "current_step" not in sprint:
            sprint["current_step"] = _normalize_sprint_step(existing.pop("sprint_step"))
    sprint = existing.get("sprint")
    if isinstance(sprint, dict) and "current_step" in sprint and not isinstance(sprint["current_step"], str):
        sprint["current_step"] = _normalize_sprint_step(sprint["current_step"])
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

    use_legacy_yaml = False
    try:
        existing_obj = parse_yaml(existing_text)
        template_obj = parse_yaml(template_text)
        if not isinstance(existing_obj, dict) or not isinstance(template_obj, dict):
            raise YamlParseError("root must be mapping")
    except Exception:
        # gate-checks.yaml など複雑 YAML は migrate.py 内の互換ローダーで処理する。
        try:
            existing_obj = _load_yaml_legacy(existing_text)
            template_obj = _load_yaml_legacy(template_text)
            use_legacy_yaml = True
        except Exception:
            # 既存 YAML が壊れている場合は保守的にそのまま返す。
            return existing_text

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

    if use_legacy_yaml:
        body = _dump_yaml_legacy(merged)
    else:
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
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7
    sys.exit(main())
