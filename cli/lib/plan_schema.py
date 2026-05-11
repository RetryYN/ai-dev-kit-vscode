#!/usr/bin/env python3
"""PLAN.yaml schema helpers for HELIX plan/gate tooling."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml_parser


PLAN_ID_RE = re.compile(r"^PLAN-[0-9]{3,}$")
MINI_PLAN_ID_RE = re.compile(r"^MPLAN-[0-9]{3,}$")
DESIGN_SHARD_DIRS = ("D-API", "D-DB", "D-ARCH", "D-TEST", "D-THREAT")


def _plan_sort_key(path: Path) -> tuple[int, str]:
    match = re.fullmatch(r"PLAN-([0-9]+)", path.stem)
    if not match:
        return (-1, path.stem)
    return (int(match.group(1)), path.stem)


def _mini_plan_sort_key(path: Path) -> tuple[int, str]:
    match = re.fullmatch(r"MPLAN-([0-9]+)", path.stem)
    if not match:
        return (-1, path.stem)
    return (int(match.group(1)), path.stem)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_plan_id(plan_id: str) -> str:
    if not PLAN_ID_RE.fullmatch(plan_id):
        raise ValueError(f"invalid plan id: {plan_id}")
    return plan_id


def validate_mini_plan_id(plan_id: str) -> str:
    if not MINI_PLAN_ID_RE.fullmatch(plan_id):
        raise ValueError(f"invalid mini plan id: {plan_id}")
    return plan_id


def validate_parent_plan_id(plan_id: str) -> str:
    if PLAN_ID_RE.fullmatch(plan_id) or MINI_PLAN_ID_RE.fullmatch(plan_id):
        return plan_id
    raise ValueError(f"invalid parent plan id: {plan_id}")


def next_mini_plan_id(mini_plans_dir: Path) -> str:
    max_num = 0
    for candidate in sorted(mini_plans_dir.glob("MPLAN-*.yaml"), key=_mini_plan_sort_key):
        match = MINI_PLAN_ID_RE.fullmatch(candidate.stem)
        if not match:
            continue
        max_num = max(max_num, int(candidate.stem.split("-", 1)[1]))
    return f"MPLAN-{max_num + 1:03d}"


def resolve_mini_plan_file(project_root: Path, plan_id: str) -> Path:
    validate_mini_plan_id(plan_id)
    return project_root / ".helix" / "mini-plans" / f"{plan_id}.yaml"


def detect_mini_plan_cycle(project_root: Path, child_plan_id: str, parent_plan_id: str) -> list[str]:
    validate_mini_plan_id(child_plan_id)
    validate_parent_plan_id(parent_plan_id)
    if child_plan_id == parent_plan_id:
        return [child_plan_id, parent_plan_id]

    chain = [child_plan_id, parent_plan_id]
    visited = {child_plan_id}
    current = parent_plan_id

    while MINI_PLAN_ID_RE.fullmatch(current):
        if current in visited:
            chain.append(current)
            return chain
        visited.add(current)
        plan_file = resolve_mini_plan_file(project_root, current)
        if not plan_file.is_file():
            return []
        data = load_plan(plan_file)
        next_parent = data.get("parent_plan_id")
        if not isinstance(next_parent, str):
            return []
        validate_parent_plan_id(next_parent)
        chain.append(next_parent)
        if next_parent == child_plan_id:
            return chain
        current = next_parent

    return []


def normalize_plan(yaml_dict: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with PLAN-020 schema list fields normalized."""
    normalized = dict(yaml_dict)
    normalized["references"] = _as_list(normalized.get("references"))
    normalized["artifacts"] = _as_list(normalized.get("artifacts"))
    return normalized


def is_legacy_plan(yaml_dict: dict[str, Any]) -> bool:
    """Legacy plans predate references/artifacts and are excluded from new G2 rules."""
    return not ("references" in yaml_dict and "artifacts" in yaml_dict)


def load_plan(plan_file: Path) -> dict[str, Any]:
    return yaml_parser.parse_yaml(plan_file.read_text(encoding="utf-8"))


def resolve_plan_file(project_root: Path, plan_id: str | None = None) -> Path | None:
    plans_dir = project_root / ".helix" / "plans"
    if plan_id:
        if not PLAN_ID_RE.fullmatch(plan_id):
            raise ValueError(f"invalid plan id: {plan_id}")
        candidate = plans_dir / f"{plan_id}.yaml"
        return candidate if candidate.is_file() else None

    phase_file = project_root / ".helix" / "phase.yaml"
    if phase_file.is_file():
        phase = yaml_parser.parse_yaml(phase_file.read_text(encoding="utf-8"))
        phase_plan_id = phase.get("plan_id")
        if isinstance(phase_plan_id, str) and PLAN_ID_RE.fullmatch(phase_plan_id):
            candidate = plans_dir / f"{phase_plan_id}.yaml"
            if candidate.is_file():
                return candidate

    candidates = sorted(plans_dir.glob("PLAN-*.yaml"), key=_plan_sort_key) if plans_dir.is_dir() else []
    return candidates[-1] if candidates else None


def count_design_shard_dirs(project_root: Path, plan_id: str) -> int:
    feature_root = project_root / "docs" / "features" / plan_id
    if not feature_root.is_dir():
        return 0
    return sum(1 for shard in DESIGN_SHARD_DIRS if (feature_root / shard).is_dir())


def evaluate_g2_design_evidence(project_root: Path, plan_id: str | None = None) -> dict[str, Any]:
    plan_file = resolve_plan_file(project_root, plan_id)
    if plan_file is None:
        return {
            "ok": True,
            "legacy": True,
            "reason": "plan_not_found",
            "plan_id": plan_id or "",
            "references_count": 0,
            "design_shard_dirs_count": 0,
            "plan_file": "",
        }

    raw_plan = load_plan(plan_file)
    resolved_plan_id = str(raw_plan.get("id") or plan_file.stem)
    if is_legacy_plan(raw_plan):
        return {
            "ok": True,
            "legacy": True,
            "reason": "legacy_plan",
            "plan_id": resolved_plan_id,
            "references_count": 0,
            "design_shard_dirs_count": 0,
            "plan_file": str(plan_file),
        }

    plan = normalize_plan(raw_plan)
    references_count = len(plan["references"])
    design_shard_dirs_count = count_design_shard_dirs(project_root, resolved_plan_id)
    ok = references_count >= 3 or design_shard_dirs_count >= 3
    return {
        "ok": ok,
        "legacy": False,
        "reason": "passed" if ok else "insufficient_g2_design_evidence",
        "plan_id": resolved_plan_id,
        "references_count": references_count,
        "design_shard_dirs_count": design_shard_dirs_count,
        "plan_file": str(plan_file),
    }


def _cmd_g2_check(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    result = evaluate_g2_design_evidence(project_root, args.plan_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["ok"]:
        if result["legacy"]:
            print(f"SKIP: legacy PLAN ({result['reason']})")
        else:
            print(
                "PASS: G2 design evidence "
                f"(references={result['references_count']}, "
                f"D-shards={result['design_shard_dirs_count']})"
            )
    else:
        print(
            "FAIL: G2 design evidence requires references >= 3 "
            "or docs/features/<plan-id>/D-* dirs >= 3 "
            f"(plan={result['plan_id']}, references={result['references_count']}, "
            f"D-shards={result['design_shard_dirs_count']})",
            file=sys.stderr,
        )
    return 0 if result["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PLAN.yaml schema helpers")
    sub = parser.add_subparsers(dest="command", required=True)
    g2 = sub.add_parser("g2-check")
    g2.add_argument("--project-root", default=".")
    g2.add_argument("--plan-id", default=None)
    g2.add_argument("--json", action="store_true")
    g2.set_defaults(func=_cmd_g2_check)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
