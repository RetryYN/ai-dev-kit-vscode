#!/usr/bin/env python3
"""HELIX setup component runner."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_NEEDS_ATTENTION = 1
EXIT_ERROR = 2
EXIT_NOT_APPLICABLE = 3
VALID_EXIT_CODES = {EXIT_SUCCESS, EXIT_NEEDS_ATTENTION, EXIT_ERROR, EXIT_NOT_APPLICABLE}
COMPONENT_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ACTIONS = ("verify", "install", "repair", "describe")


class SetupError(Exception):
    pass


class SetupArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, f"{self.prog}: error: {message}\n")


@dataclass(frozen=True)
class ComponentResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Component:
    name: str
    path: Path
    project_root: Path | None = None

    def verify(self) -> ComponentResult:
        return self._run("verify")

    def install(self) -> ComponentResult:
        return self._run("install")

    def repair(self) -> ComponentResult:
        return self._run("repair")

    def describe(self) -> ComponentResult:
        return self._run("describe")

    def _run(self, action: str) -> ComponentResult:
        if action not in ACTIONS:
            raise SetupError(f"invalid action: {action}")
        if not self.path.is_file():
            raise SetupError(f"component script not found: {self.path}")
        script = """
set -euo pipefail
source "$1"
if ! declare -F "$2" >/dev/null 2>&1; then
  echo "component function not found: $2" >&2
  exit 2
fi
"$2"
"""
        env = os.environ.copy()
        if self.project_root is not None:
            env["HELIX_PROJECT_ROOT"] = str(self.project_root)
        completed = subprocess.run(
            ["bash", "-c", script, "helix-setup-component", str(self.path), action],
            cwd=str(self.project_root or Path.cwd()),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        code = completed.returncode if completed.returncode in VALID_EXIT_CODES else EXIT_ERROR
        return ComponentResult(code, completed.stdout, completed.stderr)


def validate_component_name(name: str) -> str:
    if not name or not COMPONENT_NAME_RE.fullmatch(name):
        raise SetupError(f"invalid component name: {name}")
    return name


def discover_components(setup_dir: Path, project_root: Path | None = None) -> list[Component]:
    if not setup_dir.exists():
        return []
    if not setup_dir.is_dir():
        raise SetupError(f"setup path is not a directory: {setup_dir}")
    components = []
    for path in sorted(setup_dir.glob("*.sh")):
        name = path.stem
        if COMPONENT_NAME_RE.fullmatch(name):
            components.append(Component(name=name, path=path.resolve(), project_root=project_root))
    return components


def find_component(components: list[Component], name: str) -> Component:
    validated = validate_component_name(name)
    for component in components:
        if component.name == validated:
            return component
    raise SetupError(f"unknown component: {validated}")


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _status_name(code: int) -> str:
    return {
        EXIT_SUCCESS: "ok",
        EXIT_NEEDS_ATTENTION: "needs_attention",
        EXIT_ERROR: "error",
        EXIT_NOT_APPLICABLE: "not_applicable",
    }.get(code, "error")


def format_status_table(components: list[Component]) -> str:
    rows = ["name\tstatus\tdescription"]
    for component in components:
        verify_result = component.verify()
        describe_result = component.describe()
        description = _first_line(describe_result.stdout) if describe_result.returncode == EXIT_SUCCESS else ""
        rows.append(f"{component.name}\t{_status_name(verify_result.returncode)}\t{description}")
    return "\n".join(rows)


def format_component_list(components: list[Component]) -> str:
    rows = ["name\tdescription"]
    for component in components:
        result = component.describe()
        description = _first_line(result.stdout) if result.returncode == EXIT_SUCCESS else ""
        rows.append(f"{component.name}\t{description}")
    return "\n".join(rows)


def _print_result(result: ComponentResult) -> None:
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)


def _name_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", required=True, help="component name")


def build_parser() -> argparse.ArgumentParser:
    parser = SetupArgumentParser(description="HELIX setup component runner")
    parser.add_argument("--setup-dir", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("verify", "install", "repair"):
        _name_arg(subparsers.add_parser(command))
    subparsers.add_parser("list")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--name")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = args.project_root.resolve()
    components = discover_components(args.setup_dir.resolve(), project_root=project_root)
    try:
        if args.command == "list":
            print(format_component_list(components))
            return EXIT_SUCCESS
        if args.command == "status":
            if args.name:
                component = find_component(components, args.name)
                print(format_status_table([component]))
            else:
                print(format_status_table(components))
            return EXIT_SUCCESS
        component = find_component(components, args.name)
        result = getattr(component, args.command)()
        _print_result(result)
        return result.returncode
    except SetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
