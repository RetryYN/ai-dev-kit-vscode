#!/usr/bin/env python3
"""PLAN-006 meta-phase helpers.

Validates the fixed pattern rules used by the L1 meta-phase without adding a
new phase enum to phase.yaml.
"""

from __future__ import annotations

import argparse
import os
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import yaml_parser  # noqa: E402


VALID_PHASES = {f"L{i}" for i in range(1, 12)}
VALID_GATES = {"G0.5", "G1", "G1R", "G1.5", "G2", "G3", "G4", "G5", "G6", "G6.5", "G6.7", "G6.9", "G7", "G9", "G10", "G11"}
VALID_LAYERS = {"Plan", "Architecture", "Contract"}
VALID_CONFLICT_RESOLUTION = {"priority", "first-match", "merge", "exception"}
VALID_PATTERN_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class PatternStatus:
    path: str
    exists: bool
    pattern_count: int
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return self.exists and not self.errors


def _repo_root(start: Path | None = None) -> Path:
    if start is not None:
        return start.resolve()
    base = Path.cwd().resolve()
    for candidate in [base, *base.parents]:
        if (candidate / ".helix").exists():
            return candidate
    for env_name in ("HELIX_PROJECT_ROOT", "PROJECT_ROOT"):
        env_value = os.environ.get(env_name)
        if env_value:
            candidate = Path(env_value).expanduser().resolve()
            if (candidate / ".helix").exists() and (base == candidate or candidate in base.parents):
                return candidate
    return base


def _pattern_path(root: Path) -> Path:
    return root / ".helix" / "patterns" / "pattern.yaml"


def _as_list(value: Any, *, field: str, pattern_id: str, errors: list[str]) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    errors.append(f"{pattern_id}: {field} must be a list")
    return []


def _validate_applies_when(value: Any, pattern_id: str, errors: list[str], path: str = "applies_when") -> None:
    if not isinstance(value, dict):
        errors.append(f"{pattern_id}: {path} must be a mapping with all/any")
        return
    keys = set(value)
    if not keys <= {"all", "any"}:
        errors.append(f"{pattern_id}: {path} supports only all/any")
        return
    if not keys:
        errors.append(f"{pattern_id}: {path} must define all or any")
        return
    for key in keys:
        items = value.get(key)
        if not isinstance(items, list) or not items:
            errors.append(f"{pattern_id}: {path}.{key} must be a non-empty list")
            continue
        for index, item in enumerate(items):
            item_path = f"{path}.{key}[{index}]"
            if not isinstance(item, dict) or len(item) != 1:
                errors.append(f"{pattern_id}: {item_path} must be a single-key mapping")
                continue
            nested_key, nested_value = next(iter(item.items()))
            if nested_key in {"all", "any"}:
                _validate_applies_when({nested_key: nested_value}, pattern_id, errors, item_path)
            elif isinstance(nested_value, dict):
                errors.append(f"{pattern_id}: {item_path}.{nested_key} cannot use nested mapping")


def _validate_pattern(pattern: Any, index: int, seen_ids: set[str], errors: list[str], warnings: list[str]) -> None:
    if not isinstance(pattern, dict):
        errors.append(f"patterns[{index}]: must be a mapping")
        return
    pattern_id = str(pattern.get("id") or f"patterns[{index}]")
    if not pattern.get("id"):
        errors.append(f"{pattern_id}: id is required")
    elif not VALID_PATTERN_ID.fullmatch(pattern_id):
        errors.append(f"{pattern_id}: id must be kebab-case")
    elif pattern_id in seen_ids:
        errors.append(f"{pattern_id}: duplicate id")
    else:
        seen_ids.add(pattern_id)

    if not isinstance(pattern.get("priority"), int):
        errors.append(f"{pattern_id}: priority must be an integer")

    scope = pattern.get("scope")
    if not isinstance(scope, dict):
        errors.append(f"{pattern_id}: scope is required")
        scope = {}
    layers = _as_list(scope.get("layer"), field="scope.layer", pattern_id=pattern_id, errors=errors)
    phases = _as_list(scope.get("phase"), field="scope.phase", pattern_id=pattern_id, errors=errors)
    gates = _as_list(scope.get("gate"), field="scope.gate", pattern_id=pattern_id, errors=errors)
    subphases = _as_list(scope.get("subphase"), field="scope.subphase", pattern_id=pattern_id, errors=errors)

    if not layers:
        errors.append(f"{pattern_id}: scope.layer is required")
    if not phases:
        errors.append(f"{pattern_id}: scope.phase is required")
    if "subphase" not in scope:
        errors.append(f"{pattern_id}: scope.subphase is required")

    for layer in layers:
        if layer not in VALID_LAYERS:
            errors.append(f"{pattern_id}: invalid scope.layer {layer}")
    for phase in phases:
        if phase not in VALID_PHASES:
            errors.append(f"{pattern_id}: invalid scope.phase {phase}")
    for gate in gates:
        if gate not in VALID_GATES:
            errors.append(f"{pattern_id}: invalid scope.gate {gate}")
    for subphase in subphases:
        if not isinstance(subphase, str):
            errors.append(f"{pattern_id}: scope.subphase values must be strings")

    _validate_applies_when(pattern.get("applies_when"), pattern_id, errors)

    outputs = pattern.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        errors.append(f"{pattern_id}: outputs must be a non-empty list")
    else:
        for output_index, output in enumerate(outputs):
            if not isinstance(output, dict) or not output.get("path") or not output.get("type"):
                errors.append(f"{pattern_id}: outputs[{output_index}] requires path and type")

    conflicts = pattern.get("conflicts_with", [])
    if conflicts is None:
        conflicts = []
    if not isinstance(conflicts, list):
        errors.append(f"{pattern_id}: conflicts_with must be a list")
    else:
        for conflict_index, conflict in enumerate(conflicts):
            if not isinstance(conflict, dict):
                errors.append(f"{pattern_id}: conflicts_with[{conflict_index}] must be a mapping")
                continue
            resolution = conflict.get("resolution")
            if resolution and resolution not in VALID_CONFLICT_RESOLUTION:
                errors.append(f"{pattern_id}: invalid conflict resolution {resolution}")

    audit_log = pattern.get("audit_log")
    if not isinstance(audit_log, dict) or audit_log.get("enabled") is not True or not audit_log.get("path"):
        errors.append(f"{pattern_id}: audit_log.enabled=true and audit_log.path are required")

    exception_policy = pattern.get("exception_policy")
    if not isinstance(exception_policy, dict):
        warnings.append(f"{pattern_id}: exception_policy is not defined")


def check_patterns(root: Path | None = None) -> PatternStatus:
    resolved_root = _repo_root(root)
    path = _pattern_path(resolved_root)
    if not path.exists():
        return PatternStatus(str(path), False, 0, [f"missing pattern file: {path}"], [])
    try:
        data = yaml_parser.parse_yaml(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact parser message is unstable
        return PatternStatus(str(path), True, 0, [f"parse failed: {exc}"], [])

    errors: list[str] = []
    warnings: list[str] = []
    patterns = data.get("patterns")
    if not isinstance(patterns, list) or not patterns:
        return PatternStatus(str(path), True, 0, ["patterns must be a non-empty list"], warnings)

    seen_ids: set[str] = set()
    for index, pattern in enumerate(patterns):
        _validate_pattern(pattern, index, seen_ids, errors, warnings)
    return PatternStatus(str(path), True, len(patterns), errors, warnings)


def _print_status(status: PatternStatus) -> None:
    print("=== HELIX Meta Phase ===")
    print(f"pattern_file: {status.path}")
    print(f"exists: {'yes' if status.exists else 'no'}")
    print(f"patterns: {status.pattern_count}")
    print(f"status: {'PASS' if status.ok else 'FAIL'}")
    if status.errors:
        print("errors:")
        for error in status.errors:
            print(f"  - {error}")
    if status.warnings:
        print("warnings:")
        for warning in status.warnings:
            print(f"  - {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix meta-phase")
    parser.add_argument("--root", type=Path, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "check"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status = check_patterns(args.root)
    if args.json:
        print(json.dumps(asdict(status) | {"ok": status.ok}, ensure_ascii=False, sort_keys=True))
    else:
        _print_status(status)
    if args.command == "check":
        return 0 if status.ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
