#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

import plan_validator


def resolve_project_root(project_root: str | Path | None = None) -> Path:
    if project_root is not None:
        return Path(project_root).resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _docs_plans_dir(project_root: Path) -> Path:
    return project_root / "docs" / "plans"


def _normalize_plan_id(plan_id: str) -> str:
    return plan_id.strip()


def _normalize_artifact_path(artifact_path: str) -> str:
    return Path(artifact_path.strip()).as_posix()


def list_plan_doc_paths(project_root: str | Path | None = None) -> list[Path]:
    docs_dir = _docs_plans_dir(resolve_project_root(project_root))
    return sorted(docs_dir.glob("PLAN-*.md"))


def resolve_plan_doc_path(plan_id: str, project_root: str | Path | None = None) -> Path:
    normalized_plan_id = _normalize_plan_id(plan_id)
    docs_dir = _docs_plans_dir(resolve_project_root(project_root))
    exact = docs_dir / f"{normalized_plan_id}.md"
    if exact.is_file():
        return exact

    matches = sorted(docs_dir.glob(f"{normalized_plan_id}-*.md"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"plan markdown not found: {normalized_plan_id}")
    raise ValueError(f"multiple plan markdown files found: {normalized_plan_id}")


def load_plan_frontmatter(plan_id: str, project_root: str | Path | None = None) -> dict[str, Any]:
    path = resolve_plan_doc_path(plan_id, project_root)
    payload = plan_validator.load_frontmatter(path)
    if not isinstance(payload, dict):
        raise ValueError(f"frontmatter is not a mapping: {path}")
    return payload


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, str):
                normalized = item.strip()
                if normalized:
                    items.append(normalized)
        return items
    return []


def dependency_payload(plan_id: str, project_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    path = resolve_plan_doc_path(plan_id, root)
    frontmatter = load_plan_frontmatter(plan_id, root)
    dependencies = frontmatter.get("dependencies")
    if not isinstance(dependencies, dict):
        dependencies = {}

    return {
        "plan_id": _normalize_plan_id(plan_id),
        "doc_path": path.relative_to(root).as_posix(),
        "dependencies": {
            "parent": _string_or_none(dependencies.get("parent")),
            "requires": _string_list(dependencies.get("requires")),
            "blocks": _string_list(dependencies.get("blocks")),
        },
    }


def _child_groups(project_root: Path, plan_id: str) -> list[tuple[str, list[str]]]:
    deps = dependency_payload(plan_id, project_root)["dependencies"]
    groups: list[tuple[str, list[str]]] = []
    parent = deps["parent"]
    if parent:
        groups.append(("parent", [parent]))
    groups.append(("requires", deps["requires"]))
    groups.append(("blocks", deps["blocks"]))
    return groups


def _render_nested_dependencies(
    project_root: Path,
    plan_id: str,
    prefix: str,
    depth: int,
    seen: set[str],
) -> list[str]:
    if depth <= 0 or plan_id in seen:
        return []

    try:
        groups = _child_groups(project_root, plan_id)
    except ValueError:
        return []

    lines: list[str] = []
    visible_groups = [(name, values) for name, values in groups if values]
    next_seen = seen | {plan_id}

    for group_index, (group_name, values) in enumerate(visible_groups):
        group_last = group_index == len(visible_groups) - 1
        group_connector = "└─" if group_last else "├─"
        lines.append(f"{prefix}{group_connector} {group_name}")
        child_prefix = prefix + ("   " if group_last else "│  ")

        for value_index, dep_plan_id in enumerate(values):
            value_last = value_index == len(values) - 1
            value_connector = "└─" if value_last else "├─"
            lines.append(f"{child_prefix}{value_connector} {dep_plan_id}")
            nested_prefix = child_prefix + ("   " if value_last else "│  ")
            lines.extend(
                _render_nested_dependencies(
                    project_root,
                    dep_plan_id,
                    nested_prefix,
                    depth - 1,
                    next_seen,
                )
            )

    return lines


def render_dependency_tree(plan_id: str, depth: int = 1, project_root: str | Path | None = None) -> str:
    root = resolve_project_root(project_root)
    normalized_plan_id = _normalize_plan_id(plan_id)
    lines = [normalized_plan_id]
    lines.extend(_render_nested_dependencies(root, normalized_plan_id, "", max(depth, 1), set()))
    return "\n".join(lines)


def generates_payload(plan_id: str, project_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    path = resolve_plan_doc_path(plan_id, root)
    frontmatter = load_plan_frontmatter(plan_id, root)
    artifacts = []
    for artifact in frontmatter.get("generates") or []:
        if not isinstance(artifact, dict):
            continue
        artifact_path = _string_or_none(artifact.get("artifact_path"))
        artifact_type = _string_or_none(artifact.get("artifact_type"))
        if artifact_path and artifact_type:
            artifacts.append(
                {
                    "artifact_path": artifact_path,
                    "artifact_type": artifact_type,
                }
            )
    return {
        "plan_id": _normalize_plan_id(plan_id),
        "doc_path": path.relative_to(root).as_posix(),
        "artifacts": artifacts,
    }


def reverse_generates_lookup(artifact_path: str, project_root: str | Path | None = None) -> list[dict[str, Any]]:
    root = resolve_project_root(project_root)
    normalized_target = _normalize_artifact_path(artifact_path)
    matches: list[dict[str, Any]] = []

    for path in list_plan_doc_paths(root):
        try:
            payload = plan_validator.load_frontmatter(path)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue

        plan_id = _string_or_none(payload.get("plan_id"))
        if not plan_id:
            continue

        for artifact in payload.get("generates") or []:
            if not isinstance(artifact, dict):
                continue
            current_path = _string_or_none(artifact.get("artifact_path"))
            artifact_type = _string_or_none(artifact.get("artifact_type"))
            if not current_path or not artifact_type:
                continue
            if _normalize_artifact_path(current_path) != normalized_target:
                continue
            matches.append(
                {
                    "plan_id": plan_id,
                    "doc_path": path.relative_to(root).as_posix(),
                    "artifact_path": current_path,
                    "artifact_type": artifact_type,
                }
            )

    return sorted(matches, key=lambda item: (item["plan_id"], item["artifact_type"]))


def frontmatter_text(plan_id: str, project_root: str | Path | None = None) -> str:
    frontmatter = load_plan_frontmatter(plan_id, project_root)
    return yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PLAN frontmatter helper for deps/generates/status.")
    parser.add_argument("--project-root", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    deps_parser = subparsers.add_parser("deps")
    deps_parser.add_argument("plan_id")
    deps_parser.add_argument("--depth", type=int, default=1)
    deps_parser.add_argument("--json", action="store_true")

    generates_parser = subparsers.add_parser("generates")
    generates_parser.add_argument("plan_or_artifact", nargs="?")
    generates_parser.add_argument("--reverse", action="store_true")
    generates_parser.add_argument("--json", action="store_true")

    frontmatter_parser = subparsers.add_parser("frontmatter")
    frontmatter_parser.add_argument("plan_id")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "deps":
            payload = dependency_payload(args.plan_id, args.project_root)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(render_dependency_tree(args.plan_id, depth=args.depth, project_root=args.project_root))
            return 0

        if args.command == "generates":
            if args.reverse:
                if not args.plan_or_artifact:
                    raise ValueError("--reverse では artifact_path が必須です")
                payload = reverse_generates_lookup(args.plan_or_artifact, args.project_root)
                if args.json:
                    print(json.dumps(payload, ensure_ascii=False, indent=2))
                else:
                    print(args.plan_or_artifact)
                    if not payload:
                        print("(no matches)")
                    for item in payload:
                        print(f"- {item['plan_id']} [{item['artifact_type']}] {item['doc_path']}")
                return 0

            if not args.plan_or_artifact:
                raise ValueError("plan_id が必須です")
            payload = generates_payload(args.plan_or_artifact, args.project_root)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(payload["plan_id"])
                for artifact in payload["artifacts"]:
                    print(f"- {artifact['artifact_path']} [{artifact['artifact_type']}]")
            return 0

        if args.command == "frontmatter":
            print(frontmatter_text(args.plan_id, args.project_root))
            return 0
    except ValueError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
