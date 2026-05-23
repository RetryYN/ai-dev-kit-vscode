#!/usr/bin/env python3
"""CLI entrypoint for `helix workspace`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cli.lib.workspace_manager import (  # noqa: E402
    GitWorktreeError,
    WorkspaceDropAbortedError,
    WorkspaceExistsError,
    WorkspaceMainDirtyError,
    WorkspaceManager,
    WorkspaceMergeConflictError,
    WorkspaceMergeSubmoduleNotSupportedError,
    WorkspaceMergeTargetAheadError,
    WorkspaceNotFoundError,
    WorkspaceUntrackedFilesError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix workspace", description="Manage git worktree-based HELIX workspaces")
    parser.add_argument("--project-root", default=".", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--task", required=True)
    create_parser.add_argument("--branch")
    create_parser.add_argument("--base", default="main")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", choices=("active", "merged", "dropped"))
    list_parser.add_argument("--json", action="store_true")

    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--task", required=True)

    drop_parser = subparsers.add_parser("drop")
    drop_parser.add_argument("--task", required=True)
    drop_parser.add_argument("--force", action="store_true")

    prune_parser = subparsers.add_parser("prune")
    prune_parser.add_argument("--dry-run", action="store_true")

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--task", required=True)
    merge_parser.add_argument("--target-ref", default="main")
    merge_parser.add_argument(
        "--three-way",
        action="store_true",
        help="Use git apply --3way (allows partial conflict resolution, default False)",
    )

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("--task", required=True)
    exec_parser.add_argument("shell_command")
    return parser


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manager = WorkspaceManager(project_root=Path(args.project_root))

    try:
        if args.subcommand == "create":
            _print_json(
                manager.create(task_id=args.task, branch=args.branch, base=args.base)
            )
            return 0
        if args.subcommand == "list":
            payload = manager.list_workspaces(status=args.status)
            if args.json:
                _print_json(payload)
            else:
                for row in payload:
                    print(
                        f"{row.get('task_id')} {row.get('status')} "
                        f"{row.get('branch')} {row.get('workspace_path')}"
                    )
            return 0
        if args.subcommand == "preflight":
            _print_json(manager.preflight(args.task))
            return 0
        if args.subcommand == "drop":
            _print_json(manager.drop(args.task, force=args.force))
            return 0
        if args.subcommand == "prune":
            _print_json(manager.prune(dry_run=args.dry_run))
            return 0
        if args.subcommand == "merge":
            _print_json(
                manager.merge(
                    args.task,
                    target_ref=args.target_ref,
                    three_way=args.three_way,
                )
            )
            return 0
        if args.subcommand == "exec":
            return manager.exec_in_workspace(args.task, args.shell_command)
    except (
        WorkspaceExistsError,
        WorkspaceNotFoundError,
        WorkspaceDropAbortedError,
        WorkspaceMainDirtyError,
        WorkspaceUntrackedFilesError,
        WorkspaceMergeConflictError,
        WorkspaceMergeSubmoduleNotSupportedError,
        WorkspaceMergeTargetAheadError,
        GitWorktreeError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
