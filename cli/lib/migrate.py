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

import merge_settings
from yaml_parser import dump_yaml, parse_yaml
try:
    import yaml as _pyyaml
except Exception:  # pragma: no cover - optional dependency
    _pyyaml = None

TARGET_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "phase_yaml",
        "root": "helix_dir",
        "path": "phase.yaml",
        "template": "cli/templates/phase.yaml",
        "merge_strategy": "yaml",
        "backup_policy": "helix_backup",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked",
    },
    {
        "id": "gate_checks_yaml",
        "root": "helix_dir",
        "path": "gate-checks.yaml",
        "template": "cli/templates/gate-checks.yaml",
        "merge_strategy": "yaml",
        "backup_policy": "helix_backup",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked",
    },
    {
        "id": "doc_map_yaml",
        "root": "helix_dir",
        "path": "doc-map.yaml",
        "template": "cli/templates/doc-map.yaml",
        "merge_strategy": "yaml",
        "backup_policy": "helix_backup",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked",
    },
    {
        "id": "matrix_yaml",
        "root": "helix_dir",
        "path": "matrix.yaml",
        "template": "cli/templates/matrix.yaml",
        "merge_strategy": "yaml",
        "backup_policy": "helix_backup",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked",
    },
    {
        "id": "framework_yaml",
        "root": "helix_dir",
        "path": "framework.yaml",
        "template": "cli/templates/framework.yaml",
        "merge_strategy": "yaml",
        "backup_policy": "helix_backup",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked",
    },
    {
        "id": "claude_md",
        "root": "project_root",
        "path": "CLAUDE.md",
        "template": "cli/templates/CLAUDE.md.template",
        "merge_strategy": "text_append",
        "backup_policy": "migrate_backups",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked_or_local",
    },
    {
        "id": "agents_md",
        "root": "project_root",
        "path": "AGENTS.md",
        "template": "cli/templates/AGENTS.md.template",
        "merge_strategy": "text_append",
        "backup_policy": "migrate_backups",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "tracked_or_local",
    },
    {
        "id": "claude_settings",
        "root": "project_root",
        "path": ".claude/settings.json",
        "template": None,
        "merge_strategy": "json_hooks",
        "backup_policy": "migrate_backups_secret_isolated",
        "rollback_policy": "target_snapshot",
        "tracked_or_local": "local",
    },
]

TARGETS = {target["path"]: target["template"] for target in TARGET_REGISTRY}

VERSION_RE = re.compile(r"helix_template_version:\s*(\d+)")
FRAMEWORK_TEMPLATE_FALLBACK = """# helix_template_version: 3
detected: unknown
tools: {}
"""
MANAGED_START = "<!-- HELIX-MANAGED-START -->"
MANAGED_END = "<!-- HELIX-MANAGED-END -->"
MANIFEST_NAME = ".helix-migrate-manifest.json"


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


def resolve_project_root(helix_dir: Path, project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root
    if helix_dir.name == ".helix":
        return helix_dir.parent
    return helix_dir.parent


def resolve_target_path(target: dict[str, Any], helix_dir: Path, project_root: Path) -> Path:
    root = target["root"]
    if root == "helix_dir":
        return helix_dir / target["path"]
    if root == "project_root":
        return project_root / target["path"]
    raise ValueError(f"unknown target root: {root}")


def resolve_template_path(target: dict[str, Any], templates_dir: Path) -> Path | None:
    template = target.get("template")
    if template is None:
        return None
    template_path = Path(template)
    parts = template_path.parts
    if len(parts) >= 3 and parts[0] == "cli" and parts[1] == "templates":
        return templates_dir.joinpath(*parts[2:])
    return templates_dir / template


def _target_label(target: dict[str, Any]) -> str:
    return str(target["id"])


def _managed_block(template_text: str) -> str:
    inner = template_text
    if MANAGED_START in inner and MANAGED_END in inner:
        match = re.search(
            rf"{re.escape(MANAGED_START)}\n?(.*?)\n?{re.escape(MANAGED_END)}",
            inner,
            re.DOTALL,
        )
        if match:
            inner = match.group(1)
    return f"{MANAGED_START}\n{inner.rstrip()}\n{MANAGED_END}\n"


def merge_text_append(existing_text: str, template_text: str) -> str:
    block = _managed_block(template_text)
    if MANAGED_START in existing_text and MANAGED_END in existing_text:
        pattern = re.compile(
            rf"{re.escape(MANAGED_START)}.*?{re.escape(MANAGED_END)}\n?",
            re.DOTALL,
        )
        return pattern.sub(block, existing_text, count=1)
    if not existing_text.strip():
        return block
    return existing_text.rstrip() + "\n\n" + block


class JsonHookMergeError(ValueError):
    pass


def merge_json_hooks(existing_text: str) -> tuple[str, bool]:
    if existing_text.strip():
        try:
            current = json.loads(existing_text)
        except json.JSONDecodeError as e:
            raise JsonHookMergeError(f"invalid JSON: {e}") from e
    else:
        current = {}
    if not isinstance(current, dict):
        raise JsonHookMergeError("settings root must be object")

    merged = merge_settings.merge_settings_for_migrate(
        current,
        merge_settings.HELIX_HOOKS,
    )
    if merged == current:
        return existing_text, False
    return json.dumps(merged, ensure_ascii=False, indent=2) + "\n", True


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


def _backup_root_for_policy(helix_dir: Path, policy: str) -> Path:
    if policy == "helix_backup":
        return helix_dir / "backup"
    if policy in {"migrate_backups", "migrate_backups_secret_isolated"}:
        return helix_dir / "migrate-backups"
    raise ValueError(f"unknown backup policy: {policy}")


def _new_backup_dirs(helix_dir: Path, policies: set[str]) -> dict[str, Path]:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = 0
    while True:
        name = ts if suffix == 0 else f"{ts}-{suffix}"
        candidates = {
            policy: _backup_root_for_policy(helix_dir, policy) / name
            for policy in policies
        }
        unique_paths = set(candidates.values())
        if all(not path.exists() for path in unique_paths):
            for path in unique_paths:
                path.mkdir(parents=True, exist_ok=False)
            return candidates
        suffix += 1


def _write_backup_manifest(backup_dir: Path, entries: list[dict[str, Any]]) -> None:
    (backup_dir / MANIFEST_NAME).write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_backup(
    helix_dir: Path,
    project_root: Path | None = None,
    targets: list[dict[str, Any]] | None = None,
) -> Path:
    project_root = resolve_project_root(helix_dir, project_root)
    targets = targets if targets is not None else TARGET_REGISTRY
    policies = {target["backup_policy"] for target in targets}
    backup_dirs = _new_backup_dirs(helix_dir, policies or {"helix_backup"})
    manifest_entries: dict[Path, list[dict[str, Any]]] = {path: [] for path in backup_dirs.values()}

    for target in targets:
        src = resolve_target_path(target, helix_dir, project_root)
        backup_dir = backup_dirs[target["backup_policy"]]
        backup_rel = Path(target["path"])
        entry = {
            "id": target["id"],
            "root": target["root"],
            "path": target["path"],
            "existed": src.exists(),
            "backup_path": str(backup_rel),
        }
        if src.exists():
            dest = backup_dir / backup_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        manifest_entries[backup_dir].append(entry)

    for backup_dir, entries in manifest_entries.items():
        _write_backup_manifest(backup_dir, entries)
    return next(iter(backup_dirs.values()))


def prune_backups(helix_dir: Path, keep: int = 5) -> None:
    backup_roots = [helix_dir / "backup", helix_dir / "migrate-backups"]
    for backup_root in backup_roots:
        if not backup_root.exists():
            continue
        dirs = sorted([p for p in backup_root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
        for old in dirs[keep:]:
            shutil.rmtree(old, ignore_errors=True)


def _latest_backup_dirs(helix_dir: Path) -> list[Path]:
    backup_roots = [helix_dir / "backup", helix_dir / "migrate-backups"]
    dirs: list[Path] = []
    for backup_root in backup_roots:
        if backup_root.exists():
            dirs.extend([p for p in backup_root.iterdir() if p.is_dir()])
    if not dirs:
        raise FileNotFoundError("no backup snapshots")
    latest_name = sorted((p.name for p in dirs), reverse=True)[0]
    return sorted([p for p in dirs if p.name == latest_name])


def _target_by_id() -> dict[str, dict[str, Any]]:
    return {target["id"]: target for target in TARGET_REGISTRY}


def _restore_manifest_backup(backup_dir: Path, helix_dir: Path, project_root: Path) -> int:
    manifest_path = backup_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    targets_by_id = _target_by_id()
    restored = 0
    for entry in manifest.get("entries", []):
        target = targets_by_id.get(entry.get("id"))
        if target is None:
            continue
        dest = resolve_target_path(target, helix_dir, project_root)
        if entry.get("existed"):
            src = backup_dir / entry["backup_path"]
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                restored += 1
        else:
            if dest.exists():
                dest.unlink()
            restored += 1
    return restored


def _restore_legacy_backup(backup_dir: Path, helix_dir: Path) -> int:
    restored = 0
    for target in TARGET_REGISTRY:
        if target["root"] != "helix_dir":
            continue
        src = backup_dir / target["path"]
        if src.exists():
            dest = helix_dir / target["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            restored += 1
    return restored


def rollback(helix_dir: Path, project_root: Path | None = None) -> Path:
    project_root = resolve_project_root(helix_dir, project_root)
    latest_dirs = _latest_backup_dirs(helix_dir)
    restored = 0
    for backup_dir in latest_dirs:
        restored += _restore_manifest_backup(backup_dir, helix_dir, project_root)
        if not (backup_dir / MANIFEST_NAME).exists():
            restored += _restore_legacy_backup(backup_dir, helix_dir)
    if restored == 0:
        raise RuntimeError("latest backup has no target files")
    return latest_dirs[0]


def detect(
    helix_dir: Path,
    templates_dir: Path,
    project_root: Path | None = None,
) -> dict[str, Any]:
    project_root = resolve_project_root(helix_dir, project_root)
    result: dict[str, Any] = {}
    for target in TARGET_REGISTRY:
        current_path = resolve_target_path(target, helix_dir, project_root)
        template_path = resolve_template_path(target, templates_dir)
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else ""
        if template_path is None:
            template_text, template_exists = "", True
        else:
            try:
                template_text, template_exists = load_template_text(target["path"], template_path)
            except FileNotFoundError:
                template_text, template_exists = "", False
        result[target["path"]] = {
            "id": target["id"],
            "root": target["root"],
            "path": str(current_path),
            "template": str(template_path) if template_path is not None else None,
            "merge_strategy": target["merge_strategy"],
            "backup_policy": target["backup_policy"],
            "rollback_policy": target["rollback_policy"],
            "tracked_or_local": target["tracked_or_local"],
            "current_version": detect_template_version(current_text),
            "latest_version": detect_template_version(template_text),
            "exists": current_path.exists(),
            "template_exists": template_exists,
        }
    return result


def _merge_target(
    target: dict[str, Any],
    current_text: str,
    template_text: str,
) -> tuple[str, bool]:
    strategy = target["merge_strategy"]
    if strategy == "yaml":
        merged = merge_yaml(current_text, template_text, target["path"])
        return merged, merged != current_text
    if strategy == "text_append":
        merged = merge_text_append(current_text, template_text)
        return merged, merged != current_text
    if strategy == "json_hooks":
        return merge_json_hooks(current_text)
    raise ValueError(f"unknown merge strategy: {strategy}")


SELF_HOST_SKIP_TARGET_IDS = {"claude_md", "agents_md", "claude_settings"}


def is_helix_self_repo(project_root: Path, templates_dir: Path) -> bool:
    """Detect HELIX framework repo itself.

    本リポジトリ (cli/templates と skills/SKILL_MAP.md を持つ HELIX 本体) で migrate を
    走らせると、自身の CLAUDE.md / AGENTS.md に template が二重追記されてしまうため、
    project_root の claude_md / agents_md / claude_settings target を skip する。
    """
    try:
        templates_resolved = templates_dir.resolve()
        repo_templates = (project_root / "cli" / "templates").resolve()
    except (OSError, RuntimeError):
        return False
    return (
        (project_root / "cli" / "templates" / "CLAUDE.md.template").exists()
        and (project_root / "skills" / "SKILL_MAP.md").exists()
        and templates_resolved == repo_templates
    )


def do_merge(
    helix_dir: Path,
    templates_dir: Path,
    apply: bool,
    project_root: Path | None = None,
) -> int:
    project_root = resolve_project_root(helix_dir, project_root)
    self_repo = is_helix_self_repo(project_root, templates_dir)
    if self_repo:
        print(
            "[helix migrate] self-host detected: HELIX framework repo 自身では "
            "claude_md / agents_md / claude_settings の merge を skip します",
            file=sys.stderr,
        )
    changes = []
    for target in TARGET_REGISTRY:
        if self_repo and target["id"] in SELF_HOST_SKIP_TARGET_IDS:
            continue
        label = _target_label(target)
        current_path = resolve_target_path(target, helix_dir, project_root)
        template_path = resolve_template_path(target, templates_dir)
        if template_path is None:
            template_text = ""
        else:
            try:
                template_text, _ = load_template_text(target["path"], template_path)
            except FileNotFoundError:
                print(f"template not found: {template_path}", file=sys.stderr)
                return 2
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else ""

        current_v = detect_template_version(current_text)
        latest_v = detect_template_version(template_text)
        if (
            target["merge_strategy"] in {"yaml", "text_append"}
            and current_v is not None
            and latest_v is not None
            and current_v == latest_v
        ):
            continue

        try:
            merged_text, changed = _merge_target(target, current_text, template_text)
        except JsonHookMergeError as e:
            print(f"merge failed for {label}: {e}", file=sys.stderr)
            return 3
        except Exception as e:
            print(f"merge failed for {label}: {e}", file=sys.stderr)
            return 1

        if changed:
            diff = difflib.unified_diff(
                current_text.splitlines(keepends=True),
                merged_text.splitlines(keepends=True),
                fromfile=str(current_path),
                tofile=f"{current_path} (merged)",
            )
            changes.append((target, current_path, merged_text, "".join(diff)))

    if not changes:
        print("no changes")
        return 0

    for target, _, _, diff_text in changes:
        print(f"[{_target_label(target)}]")
        print(diff_text.rstrip())

    if not apply:
        return 0

    changed_targets = [target for target, _, _, _ in changes]
    backup = create_backup(helix_dir, project_root=project_root, targets=changed_targets)
    for _, path, merged_text, _ in changes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(merged_text, encoding="utf-8")
    prune_backups(helix_dir, keep=5)
    print(f"Backup: {backup}")
    print("Done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Migrate HELIX project targets to latest templates")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--helix-dir", type=Path, required=True, help="path to .helix directory")
    common.add_argument("--templates-dir", type=Path, required=True, help="path to templates directory")
    common.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="path to project root (default: parent of .helix)",
    )

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
    project_root: Path | None = args.project_root

    if not helix_dir.exists():
        print(f"helix dir not found: {helix_dir}", file=sys.stderr)
        return 2

    if args.command == "detect":
        data = detect(helix_dir, templates_dir, project_root=project_root)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if args.command == "merge":
        return do_merge(helix_dir, templates_dir, apply=args.apply, project_root=project_root)

    if args.command == "rollback":
        try:
            latest = rollback(helix_dir, project_root=project_root)
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
