#!/usr/bin/env python3
"""Command catalog helpers for HELIX CLI routing/help/docs checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROUTE_ARM_RE = re.compile(r"^\s*([A-Za-z0-9_-]+)(?:\|[^)]*)?\)")
EXEC_RE = re.compile(r'exec "\$SCRIPT_DIR/(helix-[A-Za-z0-9_-]+)"')
DOC_COMMAND_RE = re.compile(r"`helix ([A-Za-z0-9_-]+)`")
HELP_COMMAND_RE = re.compile(r"^\s{2}([A-Za-z0-9_-]+)\s+(.+?)\s*$")
SKIP_ARMS = {"help", "*"}


@dataclass(frozen=True)
class RouteEntry:
    name: str
    target: str | None


@dataclass(frozen=True)
class HelpEntry:
    name: str
    category: str
    description: str


@dataclass(frozen=True)
class CommandEntry:
    name: str
    category: str
    description: str
    target: str | None
    deprecated: bool


@dataclass(frozen=True)
class IntegrationContract:
    path: str
    pattern: str
    description: str


INTEGRATION_CONTRACTS = (
    IntegrationContract("cli/helix-dashboard", "R4-gap-register.yaml", "dashboard reads current reverse R4 YAML output"),
    IntegrationContract("cli/helix-dashboard", '"L9"', "dashboard has Run phase next actions"),
    IntegrationContract("cli/helix-mode", "items.values()", "scrum->forward confirmed check supports dict backlog"),
    IntegrationContract("cli/helix-reverse", "reverse.types.${TYPE}.status", "reverse R4 writes type-specific aggregate status"),
    IntegrationContract("cli/lib/team_runner.py", "helix-claude", "team runner delegates Claude members through helix claude harness"),
    IntegrationContract("cli/lib/scrum_trigger.py", "adopt_to_backlog", "scrum trigger adoption creates backlog hypotheses"),
    IntegrationContract("cli/lib/job_queue_helper.py", "worker_loop_with_recovery", "job worker requeues stale running jobs before processing"),
    IntegrationContract("cli/lib/scheduler_helper.py", "requeue_stale_older_than", "scheduler run-due requeues stale running schedules before processing"),
    IntegrationContract("cli/lib/task_dispatcher.py", 'item.endswith(" *")', "automation allowlist requires exact command or explicit wildcard"),
)


def repo_root(start: Path | None = None) -> Path:
    base = (start or Path(__file__)).resolve()
    for candidate in [base, *base.parents]:
        if (candidate / "cli" / "helix").exists() and (candidate / "docs" / "commands").exists():
            return candidate
    raise RuntimeError("repo root not found")


def parse_routes(helix_path: Path) -> dict[str, RouteEntry]:
    lines = helix_path.read_text(encoding="utf-8").splitlines()
    routes: dict[str, RouteEntry] = {}
    current: str | None = None
    block: list[str] = []

    def flush() -> None:
        nonlocal current, block
        if not current or current in SKIP_ARMS:
            current, block = None, []
            return
        target = None
        for line in block:
            match = EXEC_RE.search(line)
            if match:
                target = match.group(1)
                break
        routes[current] = RouteEntry(name=current, target=target)
        current, block = None, []

    for line in lines:
        match = ROUTE_ARM_RE.match(line)
        if match:
            flush()
            current = match.group(1)
            block = [line]
            if ";;" in line:
                flush()
            continue
        if current:
            block.append(line)
            if ";;" in line:
                flush()
    flush()
    return routes


def parse_help(helix_path: Path) -> dict[str, HelpEntry]:
    entries: dict[str, HelpEntry] = {}
    in_usage = False
    category = ""
    for raw_line in helix_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line == "Commands:":
            in_usage = True
            continue
        if not in_usage:
            continue
        if line == "Environment:" or line == "USAGE":
            break
        if not line:
            continue
        if line.endswith(":") and not line.startswith("  "):
            category = line.rstrip(":")
            continue
        command_match = HELP_COMMAND_RE.match(line)
        if command_match:
            name, description = command_match.groups()
            entries[name] = HelpEntry(name=name, category=category, description=description.strip())
    return entries


def parse_docs_index(index_path: Path) -> set[str]:
    if not index_path.exists():
        return set()
    return set(DOC_COMMAND_RE.findall(index_path.read_text(encoding="utf-8")))


def build_catalog(root: Path | None = None) -> list[CommandEntry]:
    resolved_root = root or repo_root()
    routes = parse_routes(resolved_root / "cli" / "helix")
    help_entries = parse_help(resolved_root / "cli" / "helix")
    catalog: list[CommandEntry] = []
    for name in sorted(routes):
        help_entry = help_entries.get(name)
        description = help_entry.description if help_entry else ""
        catalog.append(
            CommandEntry(
                name=name,
                category=help_entry.category if help_entry else "",
                description=description,
                target=routes[name].target,
                deprecated="deprecated" in description.lower(),
            )
        )
    return catalog


def check_catalog(root: Path | None = None) -> list[str]:
    resolved_root = root or repo_root()
    helix_path = resolved_root / "cli" / "helix"
    routes = parse_routes(helix_path)
    help_entries = parse_help(helix_path)
    docs = parse_docs_index(resolved_root / "docs" / "commands" / "index.md")
    errors: list[str] = []

    route_names = set(routes)
    help_names = set(help_entries)
    if missing := sorted(route_names - help_names):
        errors.append("help missing routed commands: " + ", ".join(missing))
    if extra := sorted(help_names - route_names):
        errors.append("help lists unrouted commands: " + ", ".join(extra))
    if missing := sorted(route_names - docs):
        errors.append("docs/commands/index.md missing routed commands: " + ", ".join(missing))
    if extra := sorted(docs - route_names):
        errors.append("docs/commands/index.md lists unrouted commands: " + ", ".join(extra))

    for name, route in sorted(routes.items()):
        if route.target is None:
            errors.append(f"route has no executable target: {name}")
            continue
        target_path = resolved_root / "cli" / route.target
        if not target_path.exists():
            errors.append(f"route target missing: {name} -> {route.target}")
        elif not target_path.is_file():
            errors.append(f"route target is not a file: {name} -> {route.target}")
    errors.extend(check_integration_contracts(resolved_root))
    return errors


def check_integration_contracts(root: Path | None = None) -> list[str]:
    resolved_root = root or repo_root()
    errors: list[str] = []
    for contract in INTEGRATION_CONTRACTS:
        target = resolved_root / contract.path
        if not target.exists():
            errors.append(f"integration contract target missing: {contract.path}")
            continue
        text = target.read_text(encoding="utf-8")
        if contract.pattern not in text:
            errors.append(f"integration contract missing: {contract.description} ({contract.path})")
    return errors


def _print_table(catalog: list[CommandEntry]) -> None:
    print("command\tcategory\ttarget\tdeprecated\tdescription")
    for entry in catalog:
        print(
            f"{entry.name}\t{entry.category}\t{entry.target or ''}\t"
            f"{str(entry.deprecated).lower()}\t{entry.description}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix commands")
    parser.add_argument("--root", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")
    check_cmd = sub.add_parser("check")
    check_cmd.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve() if args.root else repo_root()
    if args.command == "list":
        catalog = build_catalog(root)
        if args.json:
            print(json.dumps([asdict(entry) for entry in catalog], ensure_ascii=False, sort_keys=True))
        else:
            _print_table(catalog)
        return 0
    if args.command == "check":
        errors = check_catalog(root)
        if args.json:
            print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, sort_keys=True))
        elif errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
        else:
            print("PASS: command catalog is consistent")
        return 0 if not errors else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
